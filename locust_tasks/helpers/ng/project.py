import json
from locust_tasks.utilities.utils import getPath
import requests

def createProject(obj, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "projectName": projectName,
        "orgName": orgName
    }

    global projData
    with open(getPath('resources/NG/project/project.json'), 'r+') as f:
        #Updating the Json File
        projData = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(projData, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(projData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    url = "/ng/api/projects?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgName+ "&__rtag=createProject"

    if type(obj) == str:
        createProjectResponse = requests.post(obj + url, data=payload, headers=headers)
    else:
        createProjectResponse = obj.client.post(url, data=payload, headers=headers, name="CREATE PROJECT - ")
    if createProjectResponse.status_code != 200:
        print('Project Creation is failed')
        print(createProjectResponse.request.url)
        print(createProjectResponse.status_code)
        print(createProjectResponse.content)
    return createProjectResponse

def getProjectDetails(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/projects/"+projectId+"?accountIdentifier="+accountId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_PROJECT_DETAILS - "+page)
    return response

def getProjectList(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/projects?routingId="+accountId+"&accountIdentifier="+accountId+"&pageIndex=0&pageSize=10" #50
    response = self.client.get(url, headers=headers,name="GET_PROJECT_LIST - "+page)
    return response

def getProjectListUnderOrg(self, accountId, orgId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/projects?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&pageIndex=0&pageSize=10" #100
    response = self.client.get(url, headers=headers,name="GET_PROJECT_LIST_UNDER_ORG - "+page)
    return response

def getProjectDetailsMore(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/projects/"+projectId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_PROJECT_DETAILS_MORE - "+page)
    return response

def deleteProject(self, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/projects/" + projectName + "?routingId=" + accountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgName + "&__rtag=deleteProject"
    deleteProjectResponse = self.client.delete(url, headers=headers, name='Delete_Project - ')
    print(deleteProjectResponse.status_code)
    print(deleteProjectResponse.text)

def getProjectPermissionByResource(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceType": "USER",
        "permission": "core_user_invite"
    }
    with open(getPath('resources/NG/permission/permission.json'), 'r+') as f:
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

def filterProject(self, accountId, orgId, searchKeyword, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/aggregate/projects?routingId="+accountId+"&accountIdentifier="+accountId+"orgIdentifier="+orgId+"&searchTerm="+searchKeyword+"&pageIndex=0&pageSize=10" #100
    response = self.client.get(url, headers=headers,name="FILTER_PROJECT - "+page)
    return response