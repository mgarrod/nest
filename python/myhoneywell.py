#https://api.honeywell.com/oauth2/authorize?response_type=code&client_id=&redirect_uri=http://localhost
#curl -X POST https://api.honeywell.com/oauth2/token -H "Authorization: Basic ==" -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=authorization_code&code=&redirect_uri=http://localhost"

import requests
import json

refreshToken = ""
apikey = ""
authorization = ""

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

        url = "https://api.honeywell.com/v2/devices/waterLeakDetectors/83a97b81-08b4-4619-8819-e644c03bf46b/history"

        querystring = {"apikey": "FhI6TXvj4guT6XeYbGHJIGSw1mbcGN1c", "startDate": "12/1/2017", "endDate": "1/2/2018"}

        headers = {
            'authorization': "Bearer rItRBEcbzxPMfCGpkLCgF22UxWmb",
            'cache-control': "no-cache",
            'postman-token': "d5926d6e-afb5-35b7-ebc6-4b89398366f9"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)


