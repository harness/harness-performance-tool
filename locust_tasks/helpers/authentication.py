import json
import os.path

from locust.exception import StopUser

from locust_tasks.utilities.utils import getPath
import requests
import yaml
from locust import HttpUser

def getBearerToken(obj, base64UsernamePassword):
    # API TO GET THE BEARER ACCESS TOKEN
    payload = {"authorization": base64UsernamePassword}
    # print(payload)
    headers = {'Content-Type': 'application/json'}
    uri = '/api/users/login'
    if type(obj) == str:
        response = requests.post(obj + uri, data=json.dumps(payload), headers=headers)
    else:
        response = obj.client.post(uri, data=json.dumps(payload), headers=headers)

    if response.status_code != 200:
        print(response.url)
        print(response.content)
        utils.stopLocustTests()
    else:
        resp = response.content
        json_resp = json.loads(resp)
        return str(json_resp['resource']['token'])
    return None

def getAccountInfo(obj, base64UsernamePassword, authMechanism):
    payload = {"authorization": base64UsernamePassword}
    # print(payload)
    headers = {'Content-Type': 'application/json'}
    uri = '/api/users/login'
    if authMechanism.lower() == "local-login":
        uri = '/gateway/api/users/harness-local-login'
    if type(obj) == str:
        response = requests.post(obj + uri, data=json.dumps(payload), headers=headers)
    else:
        response = obj.client.post(uri, data=json.dumps(payload), headers=headers)
    if response.status_code != 200:
        print("login failure on pre-requisite data step")
        print(response.url)
        print(payload)
        print(response.content)
        utils.stopLocustTests()
    else:
        resp = response.content
        return json.loads(resp)
    return None
