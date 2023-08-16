
def getTiServiceToken(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ti-service/token?routingId="+accountId+"&accountId="+accountId
    response = self.client.get(url, headers=headers,name="GET_TI_SERVICE_TOKEN - "+page)
    return response

def getTiServiceReportSummary(self, accountId, orgId, projectId, pipelineId, buildId, tiServiceToken, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization, 'x-harness-token': tiServiceToken}
    url = "/ti-service/reports/summary?routingId="+accountId+"&accountId="+accountId+"&orgId="+orgId+"&projectId="+projectId+"&pipelineId="+pipelineId+"&buildId="+str(buildId)+"&stageId=&report=junit"
    response = self.client.get(url, headers=headers, name="GET_TI_SERVICE_REPORT_SUMMARY - "+page)
    return response
