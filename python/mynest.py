#sudo pip install --ignore-installed python-nest
#sudo pip install boto3

import requests
import json
import boto3
from botocore.exceptions import ClientError
import sys

accessToken = None
userRid = None
username = ''
password = ''

def lambda_handler(event, context):
    try:

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('nest_thermostat')

        url = "https://home.nest.com/user/login"

        payload = "username=" + username + "&password=" + password
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
        }

        response = requests.request("POST", url, data=payload, headers=headers)

        d = json.loads(response.text)
        userRid = d["user"]
        userRid = userRid[userRid.find(".") + 1:]
        accessToken = d["access_token"]

        transportUrl = d["urls"]["transport_url"]

        url = transportUrl + "/v3/mobile/user." + userRid

        headers = {
            'x-nl-user-id': userRid,
            'authorization': "Basic " + accessToken,
            'content-type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("GET", url, headers=headers)

        d = json.loads(response.text)

        structures = d["user"][userRid]["structures"]
        if len(structures) == 0:
            sendEmail(username, "No structures")
            sys.exit(0)
        for i in range(len(structures)):
            structure = structures[i]
            structure = structure[structure.find(".")+1:]
            devices = d["structure"][structure]["devices"]
            if len(devices) == 0:
                sendEmail(username, "No devices")
                sys.exit(0)
            for ii in range(len(devices)):
                device = devices[ii]
                device = device[device.find(".") + 1:]
                #device = "15AA01AC30170FLK"

                if d["device"][device]["heater_source"] != None:

                    url = transportUrl + "/v5/subscribe"

                    payload = "{\"objects\":[{\"object_key\":\"energy_latest." + device + "\"}]}"

                    response2 = requests.request("POST", url, data=payload, headers=headers)

                    d2 = json.loads(response2.text)
                    objects = d2["objects"]
                    for iii in range(len(objects)):
                        object = objects[iii]
                        days = object["value"]["days"]
                        if len(days) == 0:
                            sendEmail(username, "No days")
                            sys.exit(0)
                        for iiii in range(len(days)):
                            day = days[iiii]
                            aday = day["day"]
                            unavailable = False
                            try:
                                unavailable = day["unavailable"]
                            except:
                                unavailable = False

                            if not unavailable:
                                device_timezone_offset = day["device_timezone_offset"]
                                total_heating_time = day["total_heating_time"]
                                total_cooling_time = day["total_cooling_time"]
                                recent_avg_used = day["recent_avg_used"]
                                usage_over_avg = day["usage_over_avg"]
                                cycles = day["cycles"]
                            else:
                                device_timezone_offset = -18000
                                total_heating_time = 0
                                total_cooling_time = 0
                                recent_avg_used = 0
                                usage_over_avg = 0
                                cycles = []

                            table.put_item(
                                Item={
                                    'device': device,
                                    'day': aday,
                                    'device_timezone_offset': device_timezone_offset,
                                    'total_heating_time': total_heating_time,
                                    'total_cooling_time': total_cooling_time,
                                    'recent_avg_used': recent_avg_used,
                                    'usage_over_avg': usage_over_avg,
                                    'cycles': cycles,
                                }
                            )

                            '''
                            for iiiii in range(len(cycles)):
                                cycle = cycles[iiiii]
                                start = cycle["start"]
                                duration = cycle["duration"]
                                type = cycle["type"]
                            '''
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
    SUBJECT = "Nest History Fail"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("nest history failed to load: " + message)

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
lambda_handler(None, None)