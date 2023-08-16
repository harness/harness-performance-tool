
def getScmBranchlist(self, accountId, orgId, projectId, connRef, repoName, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ng/api/scm/list-branches?connectorRef="+connRef+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&repoName="+repoName+"&size=1"
    response = self.client.get(url, headers=headers,name="GET_SCM_BRANCH_LIST - "+page)
    return response

