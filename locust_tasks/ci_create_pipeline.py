import re
import sys
import time
import gevent
import requests
import yaml
import base64
import logging
from locust.runners import LocalRunner, MasterRunner, WorkerRunner, STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP
from locust import task, constant_pacing, SequentialTaskSet, events
from locust.runners import WorkerRunner
from locust_tasks.helpers.ng import account, organization, project, resourcegroup, \
    role, smtp, user, usergroup, gitsync, dashboard, connector, secret, pipeline, ti, log_service, \
    service, en, infra, source_code, freeze, ci_helper, template, delegate, variable
from locust_tasks.helpers import authentication
from utilities.utils import getPath, CSVReader
from utilities import utils
import csv
import json
from locust.exception import StopUser
from random import choice
from string import ascii_lowercase

uniqueId = None

def checker(environment):
    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > 0.2:
            print(f"fail ratio was {environment.runner.stats.total.fail_ratio}, quitting")
            environment.runner.quit()
            return

def ci_create_pipeline(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'ci_create_pipeline'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("ci_create_pipeline", ci_create_pipeline)

@events.test_start.add_listener
def initiator(environment, **kwargs):
    environment.runner.state = "TESTDATA SETUP"
    try:
        testdata_setup = False
        arr = utils.getTestClasses(environment)
        for ar in arr:
            try:
                getattr(sys.modules[__name__], ar)
                testdata_setup = True
            except Exception:
                pass

        if testdata_setup == True:
            global hostname
            hostname = environment.host
            env = environment.parsed_options.env

            utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))

            # pre-requisite
            # create org, project, secret, gitConn, dockerConn, k8sConn, template

            global accountId
            global uniqueId
            global projectId
            projectId = "perf_project"
            global githubConnId
            githubConnId = "perf_conn_github"
            global dockerConnId
            dockerConnId = "perf_conn_docker"
            global templateId
            templateId = "perf_template"
            global templateVersionId
            templateVersionId = "version1"
            global k8sConnId
            k8sConnId = "perf_conn_k8s_del"
            global namespace
            global delegate_tag
            delegate_tag = 'perf-delegate'
            global repoUrl
            global repoName

            # generate bearer token for test data setup
            username_list = CSVReader(getPath('data/{}/credentials.csv'.format(env)))
            creds = next(username_list)[0].split(':')
            c = creds[0] + ':' + creds[1]
            en = base64.b64encode(c.encode('ascii'))
            base64UsernamePassword = 'Basic ' + en.decode('ascii')
            json_response = authentication.getAccountInfo(hostname, base64UsernamePassword)
            bearerToken = json_response['resource']['token']
            accountId = json_response['resource']['defaultAccountId']

            # get repo url and repo name
            varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'repoUrl', bearerToken)
            json_resp = json.loads(varResponse.content)
            repoUrl = str(json_resp['data']['variable']['spec']['fixedValue'])
            repoName = re.search(r'/([^/]+?)(?:\.git)?$', repoUrl).group(1)

            # get k8s namespace
            varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'k8sNamespace', bearerToken)
            json_resp = json.loads(varResponse.content)
            namespace = str(json_resp['data']['variable']['spec']['fixedValue'])

            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                global uniqueId
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("ci_create_pipeline", uniqueId)
                print("GENERATING TEST DATA ON CI_CREATE_PIPELINE WITH UNIQUE ID - " + uniqueId)
                orgId = "auto_org_" + uniqueId
                organization.createOrg(hostname, orgId, accountId, bearerToken)
                project.createProject(hostname, projectId, orgId, accountId, bearerToken)
                connector.createDockerConnectorAnonymous(hostname, accountId, orgId, projectId, dockerConnId,
                                                         'https://index.docker.io/v2/', bearerToken)
                create_pipeline_template(hostname, templateId, templateVersionId, accountId, orgId, projectId, dockerConnId,
                                         bearerToken)
                connector.createK8sConnector_delegate(hostname, accountId, orgId, projectId, k8sConnId, delegate_tag,
                                                      bearerToken)
                # use existing harness secret eg: user0 (repo userid) | token0 (repo user token)
                connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, githubConnId, repoUrl,
                                                        'account.user0', 'account.token0', bearerToken)
    except Exception:
        logging.exception("Exception occurred while generating test data for CI_CREATE_PIPELINE")
        utils.stopLocustTests()

def create_pipeline_template(hostname, identifier, versionId, accountId, orgId, projectId, connectorRef, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/step_template_payload.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "connectorRef": connectorRef,
        "versionLabel": versionId,
        "parallelism": "2"
    }
    url = "/template/api/templates?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&comments=&isNewTemplate=true&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline template created as part of test data failed")
        print(response.url)
        print(response.content)

# User journey :
# Login → Search for Org → Search for Project → Project Details -> Select Builds from left menu ->
# -> Select Pipelines from left menu -> Create a Pipeline -> Save

# Saving non-git exp pipeline

class CI_CREATE_PIPELINE(SequentialTaskSet):

    def data_initiator(self):
        self.__class__.wait_time = constant_pacing(1 // 1)

    def authentication(self):
        creds = next(utils.userid_list)[0].split(':')
        c = creds[0] + ":" + creds[1]
        en = base64.b64encode(c.encode('ascii'))
        payload = {"authorization": 'Basic ' + en.decode('ascii')}
        headers = {'Content-Type': 'application/json'}
        uri = '/api/users/login'
        print("logging with :: " + creds[0])
        response = self.client.post(uri, data=json.dumps(payload), headers=headers, name="LOGIN - " + uri)
        if response.status_code != 200:
            print("Login request failure..")
            print(f"{response.request.url} {payload} {response.status_code} {response.content}")
            print("--------------------------")
            raise StopUser()
        else:
            resp = response.content
            json_resp = json.loads(resp)
            self.bearerToken = str(json_resp['resource']['token'])
            self.userId = str(json_resp['resource']['uuid'])
            self.accountID = str(json_resp['resource']['defaultAccountId'])

    def on_start(self):
        self.data_initiator()
        self.authentication()
        self.orgId = "auto_org_" + uniqueId

    @task
    def checkPoint_start(self):
        headers = {'Content-Type': 'application/json'}
        url = "/api/version"
        response = self.client.get(url, headers=headers, name="CI_CREATE_PIPELINE_START - ")

    @task
    def setup_data(self):
        self.pipelineId = 'ci_pipeline_' + utils.getUniqueString()

    @task(3)
    def getAccountDetails_1(self):
        response = account.getAccountDetails(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getAccountLicense_2(self):
        response = account.getAccountLicense(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getAccountPermission_3(self):
        response = account.getAccountPermission(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getAccountDetails_4(self):
        response = account.getAccountDetails(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationPermission_5(self):
        response = organization.getOrganizationPermission(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationAggregate_6(self):
        response = organization.getOrganizationListMore(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationPermissionByResource_7(self):
        response = organization.getOrganizationPermissionByResource(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def filterOrganization_8(self):
        response = organization.filterOrganization(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationAggregateByOrgId_9(self):
        response = organization.getOrganizationDetailsMore(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationDetails_10(self):
        response = organization.getOrganizationDetails(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(3)
    def getSmtpConfig_11(self):
        response = smtp.getSmtpConfig(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationList_12(self):
        response = organization.getOrganizationList(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectAggregate_13(self):
        response = project.getProjectListUnderOrg(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectPermissionByResource_14(self):
        response = project.getProjectPermissionByResource(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def filterProject_15(self):
        response = project.filterProject(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGitSyncEnabled_16(self):
        response = gitsync.getGitSyncEnabled(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectDetails_17(self):
        response = project.getProjectDetails(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectAggreateByProjectId_18(self):
        response = project.getProjectDetailsMore(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    # @task [Ng dashboard aggregator is not part of SMP]
    def getResourceOverviewCount_19(self):
        response = dashboard.getResourceOverviewCount(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getOrganizationDetails_20(self):
        response = organization.getOrganizationDetails(self, self.accountID, self.orgId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGitSyncEnabled_21(self):
        response = gitsync.getGitSyncEnabled(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    # @task [Ng dashboard aggregator is not part of SMP]
    def getDeploymentStats_22(self):
        response = dashboard.getDeploymentStats(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    # @task [Ng dashboard aggregator is not part of SMP]
    def getResourceOverviewCount_23(self):
        response = dashboard.getResourceOverviewCount(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectAggregateAll_24(self):
        response = project.getProjectList(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

##
    @task
    def getGitSyncEnabled_25(self):
        response = gitsync.getGitSyncEnabled(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(3)
    def getAccountDetails_26(self):
        response = account.getAccountDetails(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getCIUsage_27(self):
        current_epoch_time = str(int(time.time() * 1000))
        response = ci_helper.getCIUsage(self, self.accountID, current_epoch_time, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getCIBuilds_28(self):
        response = ci_helper.getCIBuilds(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionSummaryAllWithoutPagination_29(self):
        current_epoch_time = str(int(time.time() * 1000))
        response = pipeline.getPipelineExecutionSummaryAllWithoutPagination(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getCIRepoBuilds_30(self):
        current_epoch_time = str(int(time.time() * 1000))
        one_month_before_epoch_time = str(int((time.time() * 1000) - 2592000000))
        response = ci_helper.getCIRepoBuilds(self, self.accountID, self.orgId, projectId, one_month_before_epoch_time, current_epoch_time, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectAggregateAll_31(self):
        response = project.getProjectList(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getCIBuildHealth_32(self):
        current_epoch_time = str(int(time.time() * 1000))
        one_month_before_epoch_time = str(int((time.time() * 1000) - 2592000000))
        response = ci_helper.getCIBuildHealth(self, self.accountID, self.orgId, projectId, one_month_before_epoch_time,
                                             current_epoch_time, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getCIBuildExecution_33(self):
        current_epoch_time = str(int(time.time() * 1000))
        one_month_before_epoch_time = str(int((time.time() * 1000) - 2592000000))
        response = ci_helper.getCIBuildExecution(self, self.accountID, self.orgId, projectId, one_month_before_epoch_time,
                                              current_epoch_time, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getListRepos_34(self):
        response = pipeline.getPipelineListRepo(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGlobalFreezeWithBannerDetails_35(self):
        response = freeze.getGlobalFreezeWithBannerDetails(self, self.accountID, self.orgId, projectId, self.bearerToken)
        json_resp = json.loads(response.content)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineList_36(self):
        response = pipeline.getPipelineList(self, self.accountID, self.orgId, projectId, self.bearerToken)
        response_json = json.loads(response.text)
        if response_json["data"]["numberOfElements"] != 0:
            self.pId_temp = response_json["data"]["content"][0]["identifier"]
        else:
            self.pId_temp = None # no pipeline available on list
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelinePermission_37(self):
        response = pipeline.getPipelinePermissionByResource(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelinePermissionByPipelineId_38(self):
        if self.pId_temp != None:
            # check permission of existing pipeline from list above
            response = pipeline.getPipelinePermissionByPipelineId(self, self.accountID, self.orgId, projectId, self.pId_temp,
                                                              self.bearerToken)
            if response.status_code != 200:
                utils.print_error_log(response)

    @task
    def getSourceCodeManager_39(self):
        response = source_code.getSourceCodeManager(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getEnforceGitExpFlag_40(self):
        response = gitsync.getEnforeGitExperienceFlag(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGitSync_41(self):
        response = gitsync.getGitSync(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineYamlSchema_42(self):
        response = pipeline.getPipelineYamlSchema(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineYamlSchemaStrategyNode_43(self):
        response = pipeline.getPipelineYamlSchemaStrategyNode(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineTemplatePermission_44(self):
        response = pipeline.getPipelineTemplatePermission(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineVariables_45(self):
        with open(getPath('resources/NG/pipeline/pipeline_inline.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineVariables_46(self):
        with open(getPath('resources/NG/pipeline/pipeline_inline_1.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutePermission_47(self):
        response = pipeline.getPipelinePermissionById(self, self.accountID, self.orgId, projectId, self.pipelineId,
                                                      "core_pipeline_execute", self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorPermissionByResource_48(self):
        response = connector.getConnectorPermissionByResource(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListCodeRepoV2WithTypesProjectLevel_49(self):
        types = '"Git","Github","Gitlab","Bitbucket","Codecommit","AzureRepo"'
        response = connector.getConnectorListV2WithTypesProjectLevel(self, self.accountID, self.orgId, projectId, types, '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListCodeRepoV2WithTypes_50(self):
        types = '"Git", "Github", "Gitlab", "Bitbucket", "Codecommit", "AzureRepo"'
        response = connector.getConnectorListV2WithTypes(self, self.accountID, types, '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorPermissionByResourceIdEdit_51(self):
        response = connector.getConnectorPermissionByResourceIdEdit(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(3)
    def getConnectorDetailsGit_52(self):
        response = connector.getConnectorDetails(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getCIPipelineSteps_53(self):
        response = pipeline.getCIPipelineSteps(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def connectorTestConnection_54(self):
        response = connector.testConnection(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(3)
    def getPipelineVariables_55(self):
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef": githubConnId,
            "dockerConnectorRef": dockerConnId
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListV2WithTypesProjectLevel_56(self):
        types = '"Gcp","Aws","DockerRegistry","Azure"'
        response = connector.getConnectorListV2WithTypesProjectLevel(self, self.accountID, self.orgId, projectId, types, '',
                                                                     self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListV2WithTypes_57(self):
        types = '"Gcp","Aws","DockerRegistry","Azure"'
        response = connector.getConnectorListV2WithTypes(self, self.accountID, types, '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorPermissionByResourceIdEdit_58(self):
        response = connector.getConnectorPermissionByResourceIdEdit(self, self.accountID, self.orgId, projectId, dockerConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorDetailsDocker_59(self):
        response = connector.getConnectorDetails(self, self.accountID, self.orgId, projectId, dockerConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateListRepos_60(self):
        response = template.getTemplateListRepo(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateListMetaDataWithChildTypes_61(self):
        childTypes = '"ArtifactoryUpload","BuildAndPushECR","BuildAndPushDockerRegistry","BuildAndPushGCR","S3Upload","GCSUpload","BuildAndPushACR","ArtifactoryUpload","Bitrise","SaveCacheS3","BuildAndPushECR","Background","BuildAndPushDockerRegistry","BuildAndPushGCR","RunTests","BuildAndPushACR","Action","RestoreCacheGCS","RestoreCacheS3","Run","SaveCacheGCS","GitClone","Plugin","Zap","Mend","Sonarqube","Grype","PrismaCloud","Snyk","Bandit","AquaTrivy","BlackDuck","Checkmarx","Security","CI"'
        templateEntityTypes = '"Step","StepGroup"'
        response = template.getTemplateListMetaDataWithChildTypes(self, self.accountID, self.orgId, projectId, childTypes, templateEntityTypes, '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateListMetaData_62(self):
        response = template.getTemplateListMetaData(self, self.accountID, self.orgId, projectId, templateId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(3)
    def getTemplateDetails_63(self):
        response = template.getTemplateDetails(self, self.accountID, self.orgId, projectId, templateId, templateVersionId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateViewPermission_64(self):
        response = template.getTemplatePermissionByResource(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getTemplateInputs_65(self):
        response = template.getTemplateInputs(self, self.accountID, self.orgId, projectId, templateId, templateVersionId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplatePermissionViewCopy_66(self):
        response = template.getTemplatePermissionViewCopy(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateDetailsWithoutVersion_67(self):
        response = template.getTemplateDetailsWithoutVersion(self, self.accountID, self.orgId, projectId, templateId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getPipelineVariables_68(self):
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef":  githubConnId,
            "dockerConnectorRef":  dockerConnId,
            "templateRef":  templateId,
            "versionLabel": templateVersionId
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getDelegates_69(self):
        response = delegate.getDelegates(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListUnderProjectWithType_70(self):
        response = connector.getConnectorListUnderProjectWithType(self, self.accountID, self.orgId, projectId, 'K8sCluster', '',
                                                                     self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorListWithType_71(self):
        response = connector.getConnectorListWithType(self, self.accountID, 'K8sCluster', '',
                                                      self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorPermissionByResourceIdEdit_72(self):
        response = connector.getConnectorPermissionByResourceIdEdit(self, self.accountID, self.orgId, projectId, k8sConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getPipelineVariables_73(self):
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef":  githubConnId,
            "dockerConnectorRef":  dockerConnId,
            "templateRef":  templateId,
            "versionLabel": templateVersionId,
            "k8sConnectorRef":  k8sConnId,
            "namespace": namespace
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def createCIPipeline_74(self):
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef":  githubConnId,
            "dockerConnectorRef":  dockerConnId,
            "templateRef":  templateId,
            "versionLabel": templateVersionId,
            "k8sConnectorRef":  k8sConnId,
            "namespace": namespace
        }
        self.url = "/pipeline/api/pipelines/v2?accountIdentifier="+self.accountID+"&projectIdentifier="+projectId+"&orgIdentifier="+self.orgId+"&storeType=INLINE"
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "CREATE CI PIPELINE - ")
        if response.status_code != 200:
            utils.print_error_log(response)


    @task
    def getPipelineDetails_75(self):
        response = pipeline.getPipelineDetails1(self, self.accountID, self.orgId, projectId, self.pipelineId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineSummary_76(self):
        response = pipeline.getPipelineSummary1(self, self.accountID, self.orgId, projectId, self.pipelineId,
                                                        self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineEditPermission_77(self):
        response = pipeline.getPipelinePermissionById(self, self.accountID, self.orgId, projectId, self.pipelineId,
                                                      "core_pipeline_edit", self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTemplateDetailsRemote_78(self):
        response = template.getTemplateDetailsRemote(self, self.accountID, self.orgId, projectId, templateId, '', '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorDetailsGit_79(self):
        response = connector.getConnectorDetails(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getConnectorDetailsGit_80(self):
        response = connector.getConnectorDetails(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def connectorTestConnection_81(self):
        response = connector.testConnection(self, self.accountID, self.orgId, projectId, githubConnId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineVariables_82(self):
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef":  githubConnId,
            "dockerConnectorRef":  dockerConnId,
            "templateRef":  templateId,
            "versionLabel": templateVersionId,
            "k8sConnectorRef":  k8sConnId,
            "namespace": namespace
        }
        self.url = "/pipeline/api/pipelines/v2/variables?routingId=" + self.accountID + "&accountIdentifier=" + self.accountID + "&orgIdentifier=" + self.orgId + "&projectIdentifier=" + projectId
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, self.url, self.bearerToken,
                                                        "GET PIPELINE VARIABLES - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def checkPoint_end(self):
        headers = {'Content-Type': 'application/json'}
        url = "/api/version"
        response = self.client.get(url, headers=headers, name="CI_CREATE_PIPELINE_END - ")
        return response
