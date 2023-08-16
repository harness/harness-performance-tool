import json
from locust_tasks.utilities.utils import getPath

def getTemplateListRepo(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/template/api/templates/list-repo?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&includeAllTemplatesAvailableAtScope=true"
    response = self.client.get(url, headers=headers,name="GET_TEMPLATE_LIST_REPOS - "+page)
    return response

def getTemplateDetails(self, accountId, orgId, projectId, templateId, versionId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/template/api/templates/"+templateId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&versionLabel="+versionId+"&getDefaultFromOtherRepo=true"
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.get(url, headers=headers,name="GET_TEMPLATE_DETAILS - "+page)
    return response

def getTemplateDetailsRemote(self, accountId, orgId, projectId, templateId, repoId, branchId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/template/api/templates/"+templateId+"?accountIdentifier="+accountId+"&repoIdentifier="+repoId+"&branch="+branchId+"&getDefaultFromOtherRepo=true"
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.get(url, headers=headers,name="GET_TEMPLATE_DETAILS_REMOTE - "+page)
    return response

def getTemplateDetailsWithoutVersion(self, accountId, orgId, projectId, templateId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/template/api/templates/"+templateId+"?accountIdentifier="+accountId+"&storeType=INLINE&getDefaultFromOtherRepo=true"
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.get(url, headers=headers,name="GET_TEMPLATE_DETAILS_WITHOUT_VERSION - "+page)
    return response

def getTemplateInputs(self, accountId, orgId, projectId, templateId, versionId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/template/api/templates/templateInputs/"+templateId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&versionLabel="+versionId+"&getDefaultFromOtherRepo=true"
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.get(url, headers=headers,name="GET_TEMPLATE_INPUTS - "+page)
    return response

def getTemplateListMetaData(self, accountId, orgId, projectId, templateId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "Template",
        "templateIdentifiers": templateId
    }
    with open(getPath('resources/NG/template/template_list_metadata.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    url = "/template/api/templates/list-metadata?routingId="+accountId+"&accountIdentifier="+accountId+"&templateListType=All&size=100"
    if orgId != '' and projectId != '':
        url = url + "&orgIdentifier=" + orgId + "&projectIdentifier=" + projectId
    elif orgId != '':
        url = url + "&orgIdentifier=" + orgId
    response = self.client.post(url, data=payload, headers=headers, name="GET_TEMPLATE_LIST_METADATA - " + page)
    return response

def getTemplateListMetaDataWithChildTypes(self, accountId, orgId, projectId, childTypes, templateEntityTypes, searchKey, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "Template",
        "templateEntityTypes": templateEntityTypes,
        "childTypes": childTypes
    }
    with open(getPath('resources/NG/template/template_list_metadata_child_types.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    payload = payload.replace('""', '"')
    url = "/template/api/templates/list-metadata?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&templateListType=Stable&searchTerm="+searchKey+"&page=0&size=20&includeAllTemplatesAvailableAtScope=true"
    response = self.client.post(url, data=payload, headers=headers, name="GET_TEMPLATE_LIST_METADATA_WITH_CHILD_TYPES - " + page)
    return response

def getTemplatePermissionByResource(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceType": "TEMPLATE",
        "permission": "core_template_view"
    }
    with open(getPath('resources/NG/permission/permission.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    url = "/authz/api/acl?routingId=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - "+page)
    return response

def getTemplatePermissionViewCopy(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId
    }
    with open(getPath('resources/NG/template/template_permission_view_copy.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    url = "/authz/api/acl?routingId=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="CHECK_PERMISSION - "+page)
    return response