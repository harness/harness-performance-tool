
def getGlobalFreezeWithBannerDetails(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/freeze/getGlobalFreezeWithBannerDetails?routingId="+accountId+"&accountIdentifier="+accountId+"&orgId="+orgId+"&projectId="+projectId
    response = self.client.get(url, headers=headers,name="GET_GLOBAL_FREEZE_BANNER_DETAILS - "+page)
    return response

def isPipelineDeploymentDisabled(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/freeze/evaluate/shouldDisableDeployment?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&pipelineIdentifier="+pipelineId
    response = self.client.get(url, headers=headers,name="IS_PIPELINE_DEPLOYMENT_DISABLED - "+page)
    return response
