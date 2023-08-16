
def getSmtpConfig(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/smtpConfig?routingId="+accountId+"&accountId="+accountId
    response = self.client.get(url, headers=headers,name="GET_SMTP_CONFIG - "+page)
    return response

