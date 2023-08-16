import json
from locust_tasks.utilities.utils import getPath
import requests

def createOrg(obj, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "orgName": orgName,
        "accountId": accountId
    }
    global orgData
    with open(getPath('resources/NG/organization/org.json'), 'r+') as f:
        #Updating the Json File
        orgData = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(orgData, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(orgData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    # Hitting the ENTRYPOINT
    url = "/ng/api/organizations?routingId=" + accountId + "&accountIdentifier=" + accountId + "&__rtag=createOrg"

    if type(obj) == str:
        createOrgResponse = requests.post(obj + url, data=payload, headers=headers)
    else:
        createOrgResponse = obj.client.post(url, data=payload, headers=headers, name="CREATE ORGANIZATION - ")
    if createOrgResponse.status_code != 200:
        print(createOrgResponse.status_code)
        print(createOrgResponse.content)

    return createOrgResponse

def deleteOrg(self, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/organizations/" + orgName + "?routingId=" + accountId + "&accountIdentifier=" + accountId + "&__rtag=deleteOrg"
    deleteOrgResponse = self.client.delete(url, headers=headers, name='Delete_Org - ')
    print(deleteOrgResponse.status_code)
    print(deleteOrgResponse.text)

def getOrganizationList(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/organizations?accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ORGANIZATION_LIST - "+page)
    return response

def getOrganizationPermission(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "resourceType": "ORGANIZATION",
        "permission": "core_organization_create"
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

def getOrganizationListMore(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/organizations?routingId="+accountId+"&accountIdentifier="+accountId+"&pageIndex=0&pageSize=10" #30
    response = self.client.get(url, headers=headers,name="GET_ORGANIZATION_LIST_MORE - "+page)
    return response

def getOrganizationDetailsMore(self, accountId, orgId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/organizations/"+orgId+"?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ORGANIZATION_DETAILS_MORE - "+page)
    return response

def getOrganizationPermissionByResource(self, accountId, orgId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "resourceType": "USER",
        "permission": "core_user_invite"
    }
    with open(getPath('resources/NG/organization/org_permission.json'), 'r+') as f:
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

def filterOrganization(self, accountId, searchKeyword, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/organizations?routingId="+accountId+"&accountIdentifier="+accountId+"&searchTerm="+searchKeyword+"&pageIndex=0&pageSize=10" #30
    response = self.client.get(url, headers=headers,name="FILTER_ORGANIZATION - "+page)
    return response

def getOrganizationDetails(self, accountId, orgId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/organizations/"+orgId+"?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ORGANIZATION_DETAILS - "+page)
    return response