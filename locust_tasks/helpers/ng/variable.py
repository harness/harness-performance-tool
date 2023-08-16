
import requests

def getVariableDetails(obj, accountId, orgId, projectId, variableId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/variables/"+variableId+"?accountIdentifier="+accountId
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    if type(obj) == str:
        response = requests.get(obj + url, headers=headers)
    else:
        response = obj.client.get(url, headers=headers, name="GET_VARIABLE_DETAILS - " + page)
    return response
