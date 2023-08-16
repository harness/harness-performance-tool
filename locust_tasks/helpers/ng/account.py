import json
from locust_tasks.utilities.utils import getPath

def getAccountDetails(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/accounts/"+accountId+"?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ACCOUNT_DETAILS - "+page)
    return response

def getAccountLicense(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/licenses/account?routingId=" + accountId + "&accountIdentifier=" + accountId
    response = self.client.get(url, headers=headers,name="GET_ACCOUNT_LICENSE - "+page)
    return response

def getAccountPermission(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "resourceType": "ACCOUNT",
        "permission": "core_account_edit"
    }
    with open(getPath('resources/permission.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    url = "/authz/api/acl?routingId=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - " + page)
    return response

def getAccountLicenseVersion(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/licenses/versions?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.post(url, headers=headers,name="GET_ACCOUNT_LICENSE_VERSION - "+page)
    return response

def getEnforcementEnabled(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/enforcement/enabled?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ENFORCEMENT_ENABLED - "+page)
    return response
