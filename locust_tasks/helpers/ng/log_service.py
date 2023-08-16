
def getLogServiceToken(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/log-service/token?routingId="+accountId+"&accountID="+accountId
    response = self.client.get(url, headers=headers,name="GET_LOG_SERVICE_TOKEN - "+page)
    return response

def getLogServiceStream(self, accountId, orgId, projectId, pipelineId, logServiceToken, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization, 'x-harness-token': logServiceToken}
    # self.key = 'accountId%3A'+accountId+'%2ForgId%3A'+orgId+'%2FprojectId%3A'+projectId+'%2FpipelineId%3A'+pipelineId+'%2FrunSequence%3A2%2Flevel0%3Apipeline%2Flevel1%3Astages%2Flevel2%3Astage1%2Flevel3%3Aspec%2Flevel4%3Aexecution%2Flevel5%3Asteps%2Flevel6%3AliteEngineTask'
    # url = "/log-service/stream?accountID="+accountId+"&key="+self.key
    url = "/log-service/stream?accountID=" + accountId
    response = self.client.get(url, headers=headers,name="GET_LOG_SERVICE_STREAM - "+page)
    return response

def getLogServiceBlob(self, accountId, orgId, projectId, pipelineId, logServiceToken, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization, 'x-harness-token': logServiceToken}
    self.key = 'accountId%3A' + accountId + '%2ForgId%3A' + orgId + '%2FprojectId%3A' + projectId + '%2FpipelineId%3A' + pipelineId + '%2FrunSequence%3A1%2Flevel0%3Apipeline%2Flevel1%3Astages%2Flevel2%3Astage1%2Flevel3%3Aspec%2Flevel4%3Aservice'
    url = "/log-service/blob?accountID="+accountId+"&X-Harness-Token=&key="+self.key
    response = self.client.get(url, headers=headers,name="GET_LOG_SERVICE_BLOB - "+page)
    return response
