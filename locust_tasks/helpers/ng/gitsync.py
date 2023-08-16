
def getGitSyncEnabled(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/git-sync/git-sync-enabled?accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_GIT_SYNC_ENABLED - "+page)
    return response

def getGitSync(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/git-sync?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_GIT_SYNC_CONFIGS - "+page)
    return response

def getEnforeGitExperienceFlag(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/settings/enforce_git_experience?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_ENFORCE_GIT_EXP_FLAG - "+page)
    return response
