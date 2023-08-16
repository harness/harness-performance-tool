
def getCIUsage(self, accountId, timestamp, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/ci/usage/ci?routingId="+accountId+"&accountIdentifier="+accountId+"&timestamp="+timestamp
    response = self.client.get(url, headers=headers,name="GET_CI_USAGE - "+page)
    return response

def getCIBuilds(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/ci/getBuilds?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_CI_BUILDS - "+page)
    return response

def getCIRepoBuilds(self, accountId, orgId, projectId, startTime, endTime, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/ci/repositoryBuild?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&startTime="+startTime+"&endTime="+endTime
    response = self.client.get(url, headers=headers,name="GET_CI_REPO_BUILDS - "+page)
    return response

def getCIBuildHealth(self, accountId, orgId, projectId, startTime, endTime, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/ci/buildHealth?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&startTime="+startTime+"&endTime="+endTime
    response = self.client.get(url, headers=headers,name="GET_CI_BUILD_HEALTH - "+page)
    return response

def getCIBuildExecution(self, accountId, orgId, projectId, startTime, endTime, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/ci/buildExecution?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&startTime="+startTime+"&endTime="+endTime
    response = self.client.get(url, headers=headers,name="GET_CI_BUILD_EXECUTION - "+page)
    return response