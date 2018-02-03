#https://api.honeywell.com/oauth2/authorize?response_type=code&client_id=FhI6TXvj4guT6XeYbGHJIGSw1mbcGN1c&redirect_uri=http://localhost
#curl -X POST https://api.honeywell.com/oauth2/token -H "Authorization: Basic RmhJNlRYdmo0Z3VUNlhlWWJHSEpJR1N3MW1iY0dOMWM6RXB4M2lLSTAwdzd1M2lSeA==" -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=authorization_code&code=qIXZERqC&redirect_uri=http://localhost"

import requests
import json
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from decimal import *


refreshToken = ""
apikey = ""
authorization = ""

username = 'matthew.garrod@me.com'

startDate = datetime.now() - timedelta(days=7)
endDate = datetime.now()

startDate = startDate.strftime('%m/%d/%Y')
endDate = endDate.strftime('%m/%d/%Y')

# startDate = "01/01/2017"
# endDate = "02/02/2018"

def lambda_handler(event, context):
    try:

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('honeywell')

        url = "https://api.honeywell.com/oauth2/token"

        payload = "grant_type=refresh_token&refresh_token=" + refreshToken
        headers = {
            'authorization': authorization,
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url, data=payload, headers=headers)

        d = json.loads(response.text)
        access_token = d["access_token"]

        url = "https://api.honeywell.com/v1/locations"

        querystring = {"apikey":apikey}

        headers = {
            'authorization': "Bearer " + access_token,
            'cache-control': "no-cache"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        d = json.loads(response.text)

        for i in range(len(d)):
            locationID = d[i]["locationID"] # 198214

            url = "https://api.honeywell.com/v2/devices"

            querystring = {"apikey": apikey, "locationId": locationID}

            headers = {
                'authorization': "Bearer " + access_token,
                'cache-control': "no-cache"
            }

            response2 = requests.request("GET", url, headers=headers, params=querystring)

            d2 = json.loads(response2.text)

            for ii in range(len(d2)):
                deviceID = d2[ii]["deviceID"] # 83a97b81-08b4-4619-8819-e644c03bf46b
                userDefinedDeviceName = d2[ii]["userDefinedDeviceName"] # Garage

                url = "https://api.honeywell.com/v2/devices/waterLeakDetectors/" + deviceID + "/history"

                querystring = {"apikey": apikey, "startDate": "\"" + startDate + "\"", "endDate": "\"" + endDate + "\""} # does not include enddate

                headers = {
                    'authorization': "Bearer " + access_token,
                    'cache-control': "no-cache"
                }

                response3 = requests.request("GET", url, headers=headers, params=querystring)

                d3 = json.loads(response3.text)

                tmpDate = None
                tempHigh = 0.0
                tempLow = 0.0
                humidHigh = 0.0
                humidLow = 0.0
                for iii in range(len(d3)):

                    time = datetime.strptime(d3[iii]["time"], '%Y-%m-%dT%H:%M:%S')
                    humidity = d3[iii]["humidity"]
                    temperature = (float(d3[iii]["temperature"]) * 1.8) + 32

                    if tmpDate is None:
                        tmpDate = time.date()
                        tempHigh = temperature
                        tempLow = temperature
                        humidHigh = humidity
                        humidLow = humidity
                    elif tmpDate == time.date():
                        if tempHigh < temperature:
                            tempHigh = temperature
                        if tempLow > temperature:
                            tempLow = temperature
                        if humidHigh < humidity:
                            humidHigh = humidity
                        if humidLow > humidity:
                            humidLow = humidity

                        if iii == len(d3) - 1:
                            table.put_item(
                                Item={
                                    'device': deviceID,
                                    'day': tmpDate.strftime('%Y-%m-%d'),
                                    'name': userDefinedDeviceName,
                                    'humidity_high': humidHigh,
                                    'temperature_high': Decimal(str(tempHigh)),
                                    'humidity_low': humidLow,
                                    'temperature_low': Decimal(str(tempLow))
                                }
                            )

                    else:

                        table.put_item(
                            Item={
                                'device': deviceID,
                                'day': tmpDate.strftime('%Y-%m-%d'),
                                'name': userDefinedDeviceName,
                                'humidity_high': humidHigh,
                                'temperature_high': Decimal(str(tempHigh)),
                                'humidity_low': humidLow,
                                'temperature_low': Decimal(str(tempLow))
                            }
                        )

                        tmpDate = time.date()
                        tempHigh = temperature
                        tempLow = temperature
                        humidHigh = humidity
                        humidLow = humidity

    except Exception, e:
        sendEmail(username, str(e))

def sendEmail(emailAddress, message):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = emailAddress

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = emailAddress

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = "Honeywell History Fail"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Honeywell history failed to load: " + message)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId'])

# testing
#lambda_handler(None, None)









