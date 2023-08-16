import json
from locust_tasks.utilities.utils import getPath
import requests

def createInfrastructure(obj, accountId, orgId, projectId, infraId, envId, k8sConnId, namespace, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "infraId": infraId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "environmentRef": envId,
        "k8sConnId": k8sConnId,
        "namespace": namespace,
        "allowSimultaneousDeployments": "true"
    }
    with open(getPath('resources/NG/infrastructure/infrastructure.json'), 'r+') as f:
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
    url = "/ng/api/infrastructures?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_INFRA - "+page)
    return response

def createK8sDirectInfra(obj, accountId, orgId, projectId, infraId, envId, k8sConnId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "k8sInfra": infraId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "environmentRef": envId,
        "k8sConnectorRef": k8sConnId,
        "allowSimultaneousDeployments": "true"
    }
    with open(getPath('resources/NG/infrastructure/k8s_infra.json'), 'r+') as f:
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
    url = "/ng/api/infrastructures?routingId=" + accountId + "&accountIdentifier=" + accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_INFRA - " + page)
    return response