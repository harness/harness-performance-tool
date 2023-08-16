import json
from locust_tasks.utilities.utils import getPath
import requests

def getConnectorListV2(obj, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "Connector"
    }
    with open(getPath('resources/filter_type.json'), 'r+') as f:
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
    url = "/ng/api/connectors/listV2?routingId="+accountId+"&pageIndex=0&pageSize=10&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&accountIdentifier="+accountId+"&searchTerm="
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="GET_CONNECTOR_LIST_V2 - "+page)
    return response

def getConnectorListV2WithTypes(self, accountId, types, searchKey, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "Connector",
        "types": types
    }
    with open(getPath('resources/NG/connector/connector_list.json'), 'r+') as f:
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
    payload = payload.replace('""', '"')
    url = "/ng/api/connectors/listV2?accountIdentifier="+accountId+"&searchTerm="+searchKey+"&pageIndex=0&pageSize=10"
    response = self.client.post(url, data=payload, headers=headers, name="GET_CONNECTOR_LIST_V2 - " + page)
    return response

def getConnectorListV2WithTypesProjectLevel(self, accountId, orgId, projectId, types, searchKey, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "Connector",
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "types": types
    }
    with open(getPath('resources/NG/connector/connector_list_project.json'), 'r+') as f:
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
    payload = payload.replace('""', '"')
    url = "/ng/api/connectors/listV2?accountIdentifier="+accountId+"&searchTerm="+searchKey+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&pageIndex=0&pageSize=10"
    response = self.client.post(url, data=payload, headers=headers, name="GET_CONNECTOR_LIST_V2 - " + page)
    return response

def getConnectorStats(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/stats?routingId="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_STATS - "+page)
    return response

def getConnectorCatalogue(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/catalogue?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_CATALOGUE - "+page)
    return response

def connectorFilter(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/filters?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&type=Connector"
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_FILTER - "+page)
    return response

def getConnectorPermission(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId
    }
    with open(getPath('resources/NG/connector/connector_permission.json'), 'r+') as f:
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

def getConnectorPermissionDefaultSM(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId
    }
    with open(getPath('resources/NG/connector/connector_permission_default_sm.json'), 'r+') as f:
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

def getConnectorPermissionByResourceId(self, accountId, orgId, projectId, connId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceIdentifier": connId
    }
    with open(getPath('resources/NG/connector/connector_permission_by_id.json'), 'r+') as f:
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
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - "+ page)
    return response

def getConnectorPermissionByResourceIdEdit(self, accountId, orgId, projectId, connId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgId": orgId,
        "projectId": projectId,
        "resourceType": "CONNECTOR",
        "resourceIdentifier": connId,
        "permission": "core_connector_edit"
    }
    with open(getPath('resources/NG/permission/permission_by_id.json'), 'r+') as f:
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

def getConnectorPermissionByResource(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceType": "CONNECTOR",
        "permission": "core_connector_edit"
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

def validateConnectorId(self, accountId, orgId, projectId, connId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/validateUniqueIdentifier?identifier="+connId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="VALIDATE_CONNECTOR_ID - "+page)
    return response

def getConnectorListUnderProject(self, accountId, orgId, projectId, category, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&category="+category+"&searchTerm="
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_LIST_UNDER_PROJECT - "+page)
    return response

def getConnectorListWithType(self, accountId, type, searchKey, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors?accountIdentifier="+accountId+"&type="+type+"&searchTerm="+searchKey+"&pageIndex=0&pageSize=10"
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_LIST_WITH_TYPE - "+page)
    return response

def getConnectorListUnderProjectWithType(self, accountId, orgId, projectId, type, searchKey, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors?accountIdentifier="+accountId+"&type="+type+"&searchTerm="+searchKey+"&pageIndex=0&pageSize=10&projectIdentifier="+projectId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_LIST_UNDER_PROJECT_WITH_TYPE - "+page)
    return response

def createDockerConnector(obj, accountId, orgId, projectId, connId, dockerRegistryUrl, dockerUsername, dockerPwdRef, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "connectorId": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "dockerRegistryUrl": dockerRegistryUrl,
        "username": dockerUsername,
        "passwordRef": dockerPwdRef
    }
    with open(getPath('resources/NG/connector/docker_connector.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_DOCKER_CONNECTOR - "+page)
    return response

def createDockerConnectorAnonymous(obj, accountId, orgId, projectId, connId, dockerRegistryUrl, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "connectorId": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "dockerRegistryUrl": dockerRegistryUrl
    }
    with open(getPath('resources/NG/connector/docker_connector_anonymous.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_DOCKER_CONNECTOR - "+page)
    return response

def testConnection(self, accountId, orgId, projectId, connId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/testConnection/"+connId+"?accountIdentifier="+accountId
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.post(url, headers=headers,name="CONNECTOR_TEST_CONNECTION - "+page)
    return response

def getGitRepoCI(self, accountId, orgId, projectId, gitId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/"+gitId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_GIT_REPO_CI - "+page)
    return response

def getConnectorDetails(self, accountId, orgId, projectId, connId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/connectors/" + connId + "?routingId=" + accountId + "&accountIdentifier=" + accountId
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.get(url, headers=headers,name="GET_CONNECTOR_DETAILS - "+page)
    if response.status_code != 200:
        print(response.url)
        print(response.content)
    return response

def createGitConnector(obj, accountId, orgId, projectId, connId, gitUrl, gitUsername, gitPasswordRef, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "connectorId": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "gitUrl": gitUrl,
        "username": gitUsername,
        "passwordRef": gitPasswordRef
    }
    with open(getPath('resources/NG/connector/git_connector.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_GIT_CONNECTOR - "+page)
    return response

def createGithubConnector(obj, accountId, orgId, projectId, connId, githubUrl, githubUsername, githubPasswordRef, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "identifier": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "url": githubUrl,
        "username": githubUsername,
        "tokenRef": githubPasswordRef
    }
    with open(getPath('resources/NG/connector/github_connector.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_GITHUB_CONNECTOR - "+page)
    return response

def createGithubConnectorViaUserRef(obj, accountId, orgId, projectId, connId, githubUrl, githubUsernameRef, githubPasswordRef, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "identifier": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "url": githubUrl,
        "usernameRef": githubUsernameRef,
        "tokenRef": githubPasswordRef
    }
    with open(getPath('resources/NG/connector/github_connector_user_ref.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_GITHUB_CONNECTOR - "+page)
    return response

def createK8sConnector(obj, accountId, orgId, projectId, connId, masterUrl, saTokenId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "connectorId": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "masterUrl": masterUrl,
        "serviceAccountTokenRef": saTokenId
    }
    with open(getPath('resources/NG/connector/k8s_connector.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_K8S_CONNECTOR - "+page)
    return response

def createK8sConnector_delegate(obj, accountId, orgId, projectId, connId, delegateName, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "connectorId": connId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "delegateName": delegateName
    }
    with open(getPath('resources/NG/connector/k8s_connector_delegate.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId=" + accountId + "&accountIdentifier=" + accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_K8S_CONNECTOR_DEL - "+page)
    return response


def createAwsConnector(obj, bearerToken, accountId, orgId, projectId, connectorId, secretKeyId, accessKeyId, region, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "awsConnectorName": connectorId,
        "orgName": orgId,
        "projectName": projectId,
        "accessKeyRef": accessKeyId,
        "secretKeyRef": secretKeyId,
        "region": region
    }
    with open(getPath('resources/NG/connector/aws_connector.json'), 'r+') as f:
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
    url = "/ng/api/connectors?routingId=" + accountId + "&accountIdentifier=" + accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_AWS_CONNECTOR - "+page)
    return response