
def getSourceCodeManager(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/source-code-manager?routingId="+accountId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_SOURCE_CODE_MANAGER - "+page)
    return response