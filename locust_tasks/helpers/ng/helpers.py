import json
import os.path
from locust_tasks.utilities.utils import getPath
import requests
import yaml
from locust import HttpUser
defaultAccountId = "DbSRs-u5QgukRP_ODtvGkw"
# Orgs
def createOrg(orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "orgName": orgName,
        "accountId": accountId
    }
    global orgData
    with open(getPath('resources/NG/organization/org.json'), 'r+') as f:
        #Updating the Json File
        orgData = json.load(f)
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(orgData, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(orgData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    # Hitting the ENTRYPOINT
    createOrgResponse = HttpUser.client.post(
        "/ng/api/organizations?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&__rtag=createOrg",
        data=payload, headers=headers)
    if createOrgResponse.status_code != 200:
        print(createOrgResponse.status_code)
        print(createOrgResponse.content)
    return createOrgResponse.status_code



#Create Infra
def createInfra(hostname, infraName, envType, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "infraName": infraName,
        "envType": envType,
        "projectIdentifier": projectName,
        "orgName": orgName
    }
    with open(getPath('resources/infra.json'), 'r+') as f:
        infraData = json.load(f)
        f.seek(0)
        json.dump(infraData, f, indent=4)
        f.truncate()
    payload = json.dumps(infraData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    createInfraResponse = requests.put(hostname + "/ng/api/environmentsV2/upsert?routingId="+defaultAccountId+"&accountIdentifier="+accountId, data=payload, headers=headers)
    if createInfraResponse.status_code != 200:
        print('Infra Creation is failed')
        print(createInfraResponse.request.url)
        print(createInfraResponse.status_code)
        print(createInfraResponse.content)
    return createInfraResponse.status_code


def deleteOrg(self, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    deleteOrgResponse = self.client.delete(
        "/ng/api/organizations/" + orgName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&__rtag=deleteOrg",
        headers=headers, name='Delete_Org')
    print(deleteOrgResponse.status_code)
    print(deleteOrgResponse.text)


#Projects
def createProject(hostname, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "projectName": projectName,
        "orgName": orgName
    }

    global projData
    with open(getPath('resources/project.json'), 'r+') as f:
        #Updating the Json File
        projData = json.load(f)
        # projData['project']['name'] = projectName
        # projData['project']['orgIdentifier'] = orgName
        # projData['project']['identifier'] = projectName
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(projData, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(projData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    createProjectResponse = requests.post(hostname + "/ng/api/projects?routingId="+defaultAccountId+"&accountIdentifier="+accountId+"&orgIdentifier="+orgName+ "&__rtag=createProject", data=payload, headers=headers)
    if createProjectResponse.status_code != 200:
        print('Project Creation is failed')
        print(createProjectResponse.request.url)
        print(createProjectResponse.status_code)
        print(createProjectResponse.content)
    return createProjectResponse.status_code


def deleteProject(self, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    deleteProjectResponse = self.client.delete(
        "/ng/api/projects/" + projectName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgName + "&__rtag=deleteProject",
        headers=headers, name='Delete_Project')
    print(deleteProjectResponse.status_code)
    print(deleteProjectResponse.text)

#Creating a service
def createCDNG_Service(self, svcName, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "svcName": svcName,
        "projectName": projectName,
        "orgName": orgName
    }
    with open(getPath('resources/cdng_service.json'), 'r+') as f:
        svcData = json.load(f)
        f.seek(0)
        json.dump(svcData, f, indent=4)
        f.truncate()
    payload = json.dumps(svcData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    createServiceResponse = self.client.put("/ng/api/servicesV2/upsert?routingId="+defaultAccountId+"&accountIdentifier="+accountId, data=payload, headers=headers, name='Create_Service')
    if createServiceResponse.status_code != 200:
        print(createServiceResponse.content)
    return createServiceResponse.status_code

# Secrets
def createSecret(self, secretName, secretValue, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    dataMap = {
        "secretName": secretName,
        "orgName": orgName,
        "projectName": projectName,
        "secretValue": secretValue
    }
    with open(getPath('resources/secretText.json'), 'r+') as f:
        #Updating the Json File
        secretData = json.load(f)
        # secretData['secret']['name'] = secretName
        # secretData['secret']['identifier'] = secretName
        # secretData['secret']['orgIdentifier'] = orgName
        # secretData['secret']['projectIdentifier'] = projectName
        # secretData['secret']['spec']['value'] = secretValue
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(secretData, f, indent=4)
        f.truncate()  # remove remaining part
    payload = json.dumps(secretData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    createSecretResponse = self.client.post(
        "/ng/api/v2/secrets?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgName + "&projectIdentifier=" + projectName,
        data=payload, headers=headers)
    print(createSecretResponse.status_code)
    if createSecretResponse.status_code != 200:
        print(createSecretResponse.content)
    return createSecretResponse.status_code


def deleteSecret(self, secretName, projectName, orgName, accountId, bearerToken, purpose):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    deleteSecretResponse = self.client.delete(
        "/ng/api/v2/secrets/" + secretName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&__rtag=" + purpose,
        headers=headers, name=purpose)
    print(deleteSecretResponse.status_code)
    print(deleteSecretResponse.text)


# Connectors
def createDocketConnector(self, connectorName, projectName, orgName, dockerRegistryUrl, username, secretName, accountId,
                          bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    with open(getPath('resources/docker-connector.json'), 'r+') as f:
        # Updating the Json File
        dockerData = json.load(f)
        dockerData['connector']['name'] = connectorName
        dockerData['connector']['projectIdentifier'] = projectName
        dockerData['connector']['identifier'] = connectorName
        dockerData['connector']['orgIdentifier'] = orgName
        dockerData['connector']['spec']['dockerRegistryUrl'] = dockerRegistryUrl
        dockerData['connector']['spec']['auth']['spec']['username'] = username
        dockerData['connector']['spec']['auth']['spec']['passwordRef'] = secretName
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(dockerData, f, indent=4)
        f.truncate()  # remove remaining part
    # Hitting the ENTRYPOINT
    createDocketConnectorResponse = self.client.post(
        "/ng/api/connectors?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&__rtag=createDocketConnector",
        json=dockerData, headers=headers)
    print(createDocketConnectorResponse.status_code)
    print(createDocketConnectorResponse.text)
    return createDocketConnectorResponse.status_code


def deleteConnector(self, connectorName, projectName, orgName, accountId, bearerToken, purpose):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    deleteConnectorResponse = self.client.delete(
        "/ng/api/connectors/" + connectorName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgName + "&projectIdentifier=" + projectName + "&__rtag=" + purpose,
        headers=headers, name=purpose)
    print(deleteConnectorResponse.status_code)
    print(deleteConnectorResponse.text)


# Kubernetes Connector
def createK8sConnector(self, k8ConnectorName, projectName, orgName, masterUrl, userName, secretName, accountId,
                       bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    with open(getPath('resources/kubernetes-connector.json'), 'r+') as f:
        # Updating the Json File
        k8sData = json.load(f)
        k8sData['connector']['name'] = k8ConnectorName
        k8sData['connector']['projectIdentifier'] = projectName
        k8sData['connector']['identifier'] = k8ConnectorName
        k8sData['connector']['orgIdentifier'] = orgName
        k8sData['connector']['spec']['credential']['spec']['masterUrl'] = masterUrl
        k8sData['connector']['spec']['credential']['spec']['auth']['spec']['serviceAccountTokenRef'] = secretName
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(k8sData, f, indent=4)
        f.truncate()
    # Hitting the ENTRYPOINT
    createK8sConnectorResponse = self.client.post(
        "/ng/api/connectors?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&__rtag=createK8sConnector",
        json=k8sData, headers=headers)
    print(createK8sConnectorResponse.status_code)
    print(createK8sConnectorResponse.text)
    return createK8sConnectorResponse.status_code


# GitHub Connector
def createGitHubConnector(self, gitHubConnectorName, projectName, orgName, gitHubUrl, username, secretName, accountId,
                          bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    global gitHubData
    with open(getPath('resources/github-connector.json'), 'r+') as f:
        # Updating the Json File
        gitHubData = json.load(f)
        gitHubData['connector']['name'] = gitHubConnectorName
        gitHubData['connector']['projectIdentifier'] = projectName
        gitHubData['connector']['identifier'] = gitHubConnectorName
        gitHubData['connector']['orgIdentifier'] = orgName
        gitHubData['connector']['spec']['url'] = gitHubUrl
        gitHubData['connector']['spec']['authentication']['spec']['spec']['username'] = username
        gitHubData['connector']['spec']['authentication']['spec']['spec']['tokenRef'] = secretName
        f.seek(0)  # <--- should reset file position to the beginning.
        json.dump(gitHubData, f, indent=4)
        f.truncate()
    # Hitting the ENTRYPOINT
    createGitHubConnectorResponse = self.client.post(
        "/ng/api/connectors?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&__rtag=create_GITHUB_Connector",
        json=gitHubData, headers=headers)
    print(createGitHubConnectorResponse.status_code)
    print(createGitHubConnectorResponse.text)
    return createGitHubConnectorResponse.status_code


# Pipelines
def triggerPipeline(self, pipelineName, projectName, orgName, moduleName, accountId, bearerToken, payload):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    triggerPipelineResponse = self.client.post(
        "/pipeline/api/pipeline/execute/" + pipelineName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&moduleType=" + moduleName,
        data=payload, headers=headers, name='Trigger_Pipeline')
    if triggerPipelineResponse.status_code != 200:
        print(triggerPipelineResponse.content)
    return triggerPipelineResponse


def triggerPipelineWithoutPayload(self, pipelineName, projectName, orgName, moduleName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    triggerPipelineResponse = self.client.post(
        "/pipeline/api/pipeline/execute/" + pipelineName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&moduleType=" + moduleName + "&__rtag=triggerPipeline",
        headers=headers, name='Trigger_Pipeline')
    if triggerPipelineResponse.status_code != 200:
        print(triggerPipelineResponse.content)
    return triggerPipelineResponse

def triggerPipelineWithoutPayloadWithGitExp(self, pipelineName, projectName, orgName, moduleName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    triggerPipelineResponse = self.client.post(
        "/pipeline/api/pipeline/execute/" + pipelineName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&moduleType=" + moduleName + "&branch=master&parentEntityConnectorRef=GitConnector "+"&__rtag=triggerPipeline",
        headers=headers, name='Trigger_Pipeline')
    if triggerPipelineResponse.status_code != 200:
        print(triggerPipelineResponse.content)
    return triggerPipelineResponse.status_code

# used in ci_pipeline_remote_run.py
def triggerWithWebHook(self, accountId, payloadConditionValue):
    headers = {'X-GitHub-Event': 'pull_request', 'content-type':'application/json'}
    dataMap = {
        "zen": payloadConditionValue
    }
    with open(getPath('resources/NG/pipeline/ci/ci_webhook_payload.json'), 'r+') as f:
        triggerData = json.load(f)
        f.seek(0)
        json.dump(triggerData, f, indent=4)
        f.truncate()
    payload = json.dumps(triggerData)
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    triggerWithWebHookResponse = self.client.post(
        "/ng/api/webhook?accountIdentifier={}".format(accountId), data=payload,
        headers=headers, name='TriggerWebhook')
    print(triggerWithWebHookResponse.content)
    if triggerWithWebHookResponse.status_code != 200:
        print(triggerWithWebHookResponse.request.url)
        print(triggerWithWebHookResponse.content)
    return triggerWithWebHookResponse


def createPipeline(self, pipelineName, projectName, orgName, dockerConnectorName, kubernetesConnectorName, accountId,
                   bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    with open(getPath('resources/ci_pipeline.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        dataMap = {
            "pipelineName": pipelineName,
            "pipelineIdentifier": pipelineName,
            "projectIdentifier": projectName,
            "orgName": orgName,
            "dockerConnectorName": dockerConnectorName,
            "k8sConnectorName": kubernetesConnectorName
        }
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                payload = payload.replace('$' + key, dataMap[key])
    createPipelineResponse = self.client.post(
        "/pipeline/api/pipelines?accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&__rtag=createPipeline",
        data=payload, headers=headers)
    if createPipelineResponse.status_code == 200:
        print('Pipeline is created successfully')
    else:
        print(createPipelineResponse.text)
    return createPipelineResponse.status_code


def createPipelineWithYamlPayload(self, yamlPayload, dataMap, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/yaml', 'Authorization': authorization}
    if dataMap is not None:
        for key in dataMap:
            if key is not None:
                yamlPayload = yamlPayload.replace('$' + key, dataMap[key])
    createPipelineResponse = self.client.post(
        "/pipeline/api/pipelines?accountIdentifier=" + accountId + "&projectIdentifier=" + projectName + "&orgIdentifier=" + orgName + "&__rtag=createPipeline",
        data=yamlPayload, headers=headers)
    if createPipelineResponse.status_code != 200:
        print(createPipelineResponse.text)
    return createPipelineResponse.status_code


def deletePipeline(self, pipelineName, projectName, orgName, accountId, bearerToken):
    authorization = "Bearer " + bearerToken
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    deletePipelineResponse = self.client.delete(
        "/pipeline/api/pipelines/" + pipelineName + "?routingId=" + defaultAccountId + "&accountIdentifier=" + accountId + "&orgIdentifier=" + orgName + "&projectIdentifier=" + projectName + "&__rtag=deletePipeline",
        headers=headers, name='Delete_Pipeline')
    print(deletePipelineResponse.status_code)
    print(deletePipelineResponse.text)


def validateConnector(self, connectorName, projectName, orgName, accountId, bearerToken):
    authorization ="Bearer " + bearerToken
    print("authorization:" + authorization)
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    validateConnectorResponse = self.client.post(
        "/ng/api/connectors/testConnection/" + connectorName + "?routingId=" + defaultAccountId + "&accountIdentifier=" +
        accountId + "&orgIdentifier=" + orgName + "&projectIdentifier=" + projectName, headers=headers)
    print(validateConnectorResponse.status_code)
    print(validateConnectorResponse.text)

