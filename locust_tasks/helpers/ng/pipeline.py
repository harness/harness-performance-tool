import json
from locust_tasks.utilities.utils import getPath
import requests

# this method can be used for various endpoints by providing required parameters
def postPipelineWithYamlPayload(obj, yamlPayload, dataMap, url, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                yamlPayload = yamlPayload.replace('$' + key, dataMap[key])
    if type(obj) == str:
        response = requests.post(obj + url, data=yamlPayload, headers=headers)
    else:
        response = obj.client.post(url, data=yamlPayload, headers=headers, name="" + page)
    if response.status_code != 200:
        print("POST request failure..")
        print(response.status_code)
        print(response.request.url)
        print(yamlPayload)
        print(response.content)
        print("--------------------------")
    return response


def putPipelineWithYamlPayload(obj, yamlPayload, dataMap, url, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                yamlPayload = yamlPayload.replace('$' + key, dataMap[key])
    if type(obj) == str:
        response = requests.put(obj + url, data=yamlPayload, headers=headers)
    else:
        response = obj.client.put(url, data=yamlPayload, headers=headers, name="" + page)
    return response

def getPipelineListRepo(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/list-repos?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_LIST_REPOS - "+page)
    return response

def getPipelineExecutionListRepo(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/execution/list-repositories?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_EXECUTION_LIST_REPOS - "+page)
    return response

def getPipelineList(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "PipelineSetup"
    }
    with open(getPath('resources/filter_type.json'), 'r+') as f:
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
    url = "/pipeline/api/pipelines/list?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&page=0&sort=lastUpdatedAt%2CDESC&size=20"
    response = self.client.post(url, data=payload, headers=headers, name="GET_PIPELINE_LIST - "+page)
    return response

def getPipelineListFilter(self, accountId, orgId, projectId, searchKeyword, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "filterType": "PipelineSetup"
    }
    with open(getPath('resources/filter_type.json'), 'r+') as f:
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
    url = "/pipeline/api/pipelines/list?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&page=0&sort=lastUpdatedAt%2CDESC&size=20&searchTerm="+searchKeyword
    response = self.client.post(url, data=payload, headers=headers, name="GET_PIPELINE_LIST_FILTER - "+page)
    return response

def getPipelinePermissionByResource(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceType": "PIPELINE",
        "permission": "core_pipeline_edit"
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

def getPipelinePermissionById(self, accountId, orgId, projectId, pipelineId, permissionId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountId": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceType": "PIPELINE",
        "resourceIdentifier": pipelineId,
        "permission": permissionId
    }
    with open(getPath('resources/NG/permission/permission_by_id.json'), 'r+') as f:
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

def getPipelinePermissionByPipelineId(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceIdentifier": pipelineId
    }
    with open(getPath('resources/NG/pipeline/pipeline_permission_by_id.json'), 'r+') as f:
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

def getPipelinePermissionByPipelineIdEditExecute(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceIdentifier": pipelineId
    }
    with open(getPath('resources/NG/pipeline/pipeline_permission_by_id_edit_execute.json'), 'r+') as f:
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

def getPipelineTemplatePermission(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId
    }
    with open(getPath('resources/NG/template/template_permission_edit_pipeline_execute.json'), 'r+') as f:
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

def getPipelineTemplatePermission1(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "accountIdentifier": accountId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "resourceIdentifier": pipelineId
    }
    with open(getPath('resources/NG/template/template_permission_edit_pipeline_edit.json'), 'r+') as f:
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

def getPipelineDetails(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/"+pipelineId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&getTemplatesResolvedPipeline=true"
    response = self.client.get(url, headers=headers, name="GET_PIPELINE_DETAILS - "+page)
    return response

def getPipelineDetails1(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/"+pipelineId+"?&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers, name="GET_PIPELINE_DETAILS - "+page)
    return response

def getPipelineDetails_remote(self, accountId, orgId, projectId, pipelineId, branch, parentEntityConnectorRef, parentEntityRepoName, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/"+pipelineId+"?accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&branch="+branch+"&parentEntityConnectorRef="+parentEntityConnectorRef+"&parentEntityRepoName="+parentEntityRepoName
    response = self.client.get(url, headers=headers, name="GET_PIPELINE_DETAILS_REMOTE - "+page)
    return response

def getPipelineInputSetTemplate(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    with open(getPath('resources/NG/pipeline/input_set_template.json'), 'r+') as f:
        # Updating the Json File
        data = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(data)
    url = "/pipeline/api/inputSets/template?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&pipelineIdentifier="+pipelineId
    response = self.client.post(url, data=payload, headers=headers, name="GET_PIPELINE_INPUT_SET_TEMPLATE - "+page)
    return response

def getPipelineStagesExecutionList(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipeline/execute/stagesExecutionList?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&pipelineIdentifier="+pipelineId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_STAGE_EXECUTION_LIST - "+page)
    return response

def getPipelinePreFlightCheckResponse(self, accountId, orgId, projectId, preFlightCheckId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipeline/execute/getPreflightCheckResponse?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&preflightCheckId="+preFlightCheckId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_PRE_FLIGHT_CHECK_RESPONSE - "+page)
    return response

# change name of this method to pipelineSummary after checking in plng_* files once
def getPipelineExecutionSummary(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/summary/"+pipelineId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&getMetadataOnly=true"
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_EXECUTION_SUMMARY - "+page)
    return response

def getPipelineSummary1(self, accountId, orgId, projectId, pipelineId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/summary/"+pipelineId+"?&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&getMetadataOnly=true"
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_SUMMARY - "+page)
    return response

def getPipelineExecutionSummaryAll(obj, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/execution/summary?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&page=0&size=20&sort=startTs%2CDESC"
    if type(obj) == str:
        response = requests.post(obj + url, headers=headers)
    else:
        response = obj.client.post(url, headers=headers, name="GET_PIPELINE_EXECUTION_SUMMARY_ALL - "+page)
    return response

def getPipelineExecutionSummaryAllWithoutPagination(obj, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/execution/summary?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId
    if type(obj) == str:
        response = requests.post(obj + url, headers=headers)
    else:
        response = obj.client.post(url, headers=headers, name="GET_PIPELINE_EXECUTION_SUMMARY_ALL_NO_PAGINATION - "+page)
    return response

def getPipelineExecutionSummaryFilter(self, accountId, orgId, projectId, searchKeyword, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/execution/summary?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&page=0&size=20&sort=startTs%2CDESC&searchTerm="+searchKeyword
    response = self.client.post(url, headers=headers,name="GET_PIPELINE_EXECUTION_SUMMARY_FILTER - "+page)
    return response

def getPipelineExecutionV2(self, accountId, orgId, projectId, pipelineExecutionId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipelines/execution/v2/"+pipelineExecutionId+"?routingId="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId+"&accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_EXECUTION - "+page)
    return response

def getCustomerConfig_CI(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/execution-config/get-customer-config?accountIdentifier="+accountId+"&infra=K8&overridesOnly=true"
    response = self.client.get(url, headers=headers,name="GET_CUSTOMER_CONFIG_CI - "+page)
    return response

def getDeprecatedConfig(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/ci/execution-config/get-deprecated-config?accountIdentifier="+accountId
    response = self.client.get(url, headers=headers,name="GET_DEPRECATED_CONFIG - "+page)
    return response

def getPipelineExecutionRetryHistory(self, accountId, orgId, projectId, pipelineId, pipelineExecutionId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/pipeline/execute/retryHistory/"+pipelineExecutionId+"?routingId="+accountId+"&pipelineIdentifier="+pipelineId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgId+"&projectIdentifier="+projectId
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_EXECUTION_RETRY_HISTORY - "+page)
    return response

def getPipelineYamlSchema(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/yaml-schema?routingId="+accountId+"&entityType=Pipelines"+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&accountIdentifier="+accountId+"&scope=project"
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_YAML_SCHEMA - "+page)
    return response

def getPipelineYamlSchemaStrategyNode(self, accountId, orgId, projectId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    url = "/pipeline/api/yaml-schema/get?routingId="+accountId+"&entityType=StrategyNode"+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&accountIdentifier="+accountId+"&scope=project&yamlGroup=STEP"
    response = self.client.get(url, headers=headers,name="GET_PIPELINE_YAML_SCHEMA_STRATEGY_NODE - "+page)
    return response

def getCIPipelineSteps(self, accountId, bearerToken, page=''):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "module": "ci"
    }
    with open(getPath('resources/NG/pipeline/pipeline_steps.json'), 'r+') as f:
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
    url = "/pipeline/api/pipelines/v2/steps?routingId=" + accountId + "&accountId=" + accountId
    response = self.client.post(url, data=payload, headers=headers, name="GET_CI_PIPELINE_STEPS - "+page)
    return response