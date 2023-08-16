import json
from locust_tasks.utilities.utils import getPath

def createUserGroup(self, accountId, usergroupId, userId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "usergroupId": usergroupId,
        "userId": userId
    }
    with open(getPath('resources/user_group.json'), 'r+') as f:
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
    url = "/ng/api/user-groups?routingId=" + accountId+ "&accountIdentifier=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="CREATE_USER_GROUP - "+page)
    return response

def getUserGroupList(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/acl/usergroups?routingId="+accountId+"&accountIdentifier="+accountId+"&pageIndex=0&pageSize=10&filterType=INCLUDE_INHERITED_GROUPS"
    response = self.client.get(url, headers=headers,name="GET_USER_GROUP_LIST - "+page)
    return response

def getUserGroupPermissionByResource(self, accountId, resourceId, bearerToken, page=''): # multi
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "resourceType": "USERGROUP",
        "resourceIdentifier": resourceId,
        "permission": "core_usergroup_manage"
    }
    with open(getPath('resources/resource_permission.json'), 'r+') as f:
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

def getUserGroupPermission(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "resourceType": "USERGROUP",
        "permission": "core_usergroup_manage"
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
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - "+page)
    return response