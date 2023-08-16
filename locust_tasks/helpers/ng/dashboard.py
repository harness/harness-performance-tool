
def getResourceOverviewCount(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng-dashboard/api/overview/resources-overview-count?routingId="+accountId+"&accountIdentifier="+accountId+"&startTime=1675150924200&endTime=1709365978000&projectIdentifier="+projectId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_RESOURCE_OVERVIEW_COUNT - "+page)
    return response

def getDeploymentStats(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng-dashboard/api/overview/deployment-stats?routingId="+accountId+"&accountIdentifier="+accountId+"&startTime=1675227466954&endTime=1740980729000&groupBy=DAY&sortBy=DEPLOYMENTS&projectIdentifier="+projectId+"&orgIdentifier="+orgId
    response = self.client.get(url, headers=headers,name="GET_DEPLOYMENT_STATS - "+page)
    return response
