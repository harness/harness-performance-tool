import json
from locust_tasks.utilities.utils import getPath
import requests


def getSecretList(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/v2/secrets?accountIdentifier="+accountId+"&type=SecretText&searchTerm=&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&pageIndex=0&pageSize=10&includeAllSecretsAccessibleAtScope=true"
    response = self.client.get(url, headers=headers, name="GET_SECRET_LIST - "+page)
    return response

def getSecretListProjectScope(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/v2/secrets?accountIdentifier="+accountId+"&type=SecretText&searchTerm=&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&pageIndex=0&pageSize=10&includeAllSecretsAccessibleAtScope=false"
    response = self.client.get(url, headers=headers, name="GET_SECRET_LIST_PROJECT_SCOPE - "+page)
    return response

def createSecretInline(self, accountId, orgId, projectId, secretId, secretValue, smId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "secretIdentifier": secretId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "value": secretValue,
        "secretManagerIdentifier": smId
    }
    with open(getPath('resources/NG/secret/secret_inline.json'), 'r+') as f:
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
    url = "/ng/api/v2/secrets?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.post(url, data=payload, headers=headers, name="CREATE_SECRET - "+page)
    return response

def createSecretInline(obj, accountId, orgId, projectId, secretId, secretValue, smId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "secretIdentifier": secretId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "value": secretValue,
        "secretManagerIdentifier": smId
    }
    filePath = None
    url = None
    if orgId == '' and projectId == '':
        filePath = 'resources/NG/secret/secret_inline_account.json'
        url = "/ng/api/v2/secrets?routingId=" + accountId + "&accountIdentifier=" + accountId
    elif orgId != '' and projectId != '':
        filePath = 'resources/NG/secret/secret_inline.json'
        url = "/ng/api/v2/secrets?routingId=" + accountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    else:
        return

    with open(getPath(filePath), 'r+') as f:
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
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_SECRET_INLINE - "+page)
    return response

def getSecretPermissionByResourceId(self, accountId, orgId, projectId, secretId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceIdentifier": secretId
    }
    with open(getPath('resources/NG/secret/secret_permission_by_id.json'), 'r+') as f:
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
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - "+page)
    return response