import json
from locust_tasks.utilities.utils import getPath
import requests

def createEnvironment(obj, accountId, orgId, projectId, envName, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "envName": envName,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId
    }
    with open(getPath('resources/NG/environment/environment.json'), 'r+') as f:
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
    url = "/ng/api/environmentsV2?routingId="+accountId+"&accountIdentifier="+accountId
    if type(obj) == str:
        response = requests.post(obj + url, data=payload, headers=headers)
    else:
        response = obj.client.post(url, data=payload, headers=headers, name="CREATE_ENVIRONMENT - "+page)
    return response
