
def getDelegates(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/api/setup/delegates/ng/v2?routingId="+accountId+"&accountId="+accountId
    response = self.client.get(url, headers=headers,name="GET_DELEGATES - "+page)
    return response
