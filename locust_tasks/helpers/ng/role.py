import json
from locust_tasks.utilities.utils import getPath


def assignRole(self, accountId, resourceGroupIdentifier, roleIdentifier, identifier, type, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "resourceGroupIdentifier": resourceGroupIdentifier,
        "roleIdentifier": roleIdentifier,
        "identifier": identifier,
        "type": type
    }
    with open(getPath('resources/assign_role.json'), 'r+') as f:
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
    url = "/authz/api/roleassignments/multi?routingId=" + accountId+ "&accountIdentifier=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="ASSIGN_ROLE - "+page)
    return response

def getRoles(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/authz/api/roles?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_ROLES - "+page)
    return response


