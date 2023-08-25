import json
from locust_tasks.utilities.utils import getPath
import requests

def createService(obj, accountId, orgId, projectId, gitConnId, repoBranchName, dockerConnId, serviceName, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "serviceName": serviceName,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "gitConnId": gitConnId,
        "dockerConnId": dockerConnId,
        "branch": repoBranchName
    }
    with open(getPath('resources/NG/service/service.json'), 'r+') as f:
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
    url = "/ng/api/servicesV2?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_SERVICE - "+page)
    return response



def createK8sSvcWithRuntimeGHConnectorAndEcrConnector(obj, accountId, orgId, projectId, bearerToken, serviceName, manifestCommitId, artifactConnRef, artifactImage, artifactTag, artifactRegion, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "svcName": serviceName,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "manifestConnectorRef": "<+input>",
        "commitId": manifestCommitId,
        "artifactConnectorRef": artifactConnRef,
        "artifactImage": artifactImage,
        "artifactTag": artifactTag,
        "artifactRegion": artifactRegion,
    }
    with open(getPath('resources/NG/service/k8sServiceV2.json'), 'r+') as f:
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
    url = "/ng/api/servicesV2?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_K8S_SERVICE - "+page)
    return response
