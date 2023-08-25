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
    service, en, infra, source_code, freeze, variable
from locust_tasks.helpers import authentication
from utilities.utils import getPath, CSVReader
from utilities import utils
import csv
import json
from locust.exception import StopUser
from random import choice
from string import ascii_lowercase
from concurrent.futures import ThreadPoolExecutor

uniqueId = None

def checker(environment):
    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > 0.2:
            print(f"fail ratio was {environment.runner.stats.total.fail_ratio}, quitting")
            environment.runner.quit()
            return

def ci_view_execution(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'ci_view_execution'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("ci_view_execution", ci_view_execution)

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
            # create org, project, secret, gitConn, dockerConn, template, non-git pipeline, execute pipeline

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

            # get repo branch name
            varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'repoBranchName', bearerToken)
            json_resp = json.loads(varResponse.content)
            repoBranchName = str(json_resp['data']['variable']['spec']['fixedValue'])

            # get k8s namespace
            varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'k8sNamespace', bearerToken)
            json_resp = json.loads(varResponse.content)
            namespace = str(json_resp['data']['variable']['spec']['fixedValue'])

            # create ci pipelines to view execution
            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                global uniqueId
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("ci_view_execution", uniqueId)
                print("GENERATING TEST DATA ON CI_VIEW_EXECUTION WITH UNIQUE ID - " + uniqueId)
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
                def concurrent_task():
                    pid = create_ci_pipeline(hostname, accountId, orgId, projectId, githubConnId, k8sConnId, dockerConnId,
                                             templateId, templateVersionId, namespace, bearerToken)
                    execute_ci_pipeline(hostname, accountId, orgId, projectId, pid, bearerToken)

                pipeline_count = 10
                for _ in range(10):
                    executor = ThreadPoolExecutor(max_workers=pipeline_count)
                    futures = []
                    for _ in range(pipeline_count):
                        future = executor.submit(concurrent_task)
                        futures.append(future)
                    for future in futures:
                        future.result()
                    executor.shutdown()
                    time.sleep(1)
    except Exception:
        logging.exception("Exception occurred while generating test data for CI_VIEW_EXECUTION")
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
        utils.print_error_log(response)

def create_ci_pipeline(hostname, accountId, orgId, projectId, githubConnId, k8sConnId, dockerConnId, templateId,
                       templateVersionId, namespace, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": 'ci_pipeline_for_view_exec_' + utils.getUniqueString(),
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "gitConnectorRef": githubConnId,
        "dockerConnectorRef": dockerConnId,
        "templateRef": templateId,
        "versionLabel": templateVersionId,
        "k8sConnectorRef": k8sConnId,
        "namespace": namespace
    }
    url = "/pipeline/api/pipelines/v2?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline created as part of test data failed")
        utils.print_error_log(response)
    jsonData = json.loads(response.content)
    return str(jsonData['data']['identifier'])

def execute_ci_pipeline(hostname, accountId, orgId, projectId, pipelineId, bearerToken):
    with open(getPath('resources/NG/pipeline/inputs_codebase.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "pipelineId": pipelineId,
        "branch": repoBranchName
    }
    url = "/pipeline/api/pipeline/execute/"+pipelineId+"?routingId="+accountId+"&accountIdentifier="+accountId+"&projectIdentifier="+projectId+"&orgIdentifier="+orgId+"&moduleType=&notifyOnlyUser=false"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline executed as part of test data failed")
        utils.print_error_log(response)


# User journey :
# Login → Search for Org → Search for Project → Project Details -> Select Pipeline Execution from left menu ->
# -> Search for execution -> Open the execution and view status

class CI_VIEW_EXECUTION(SequentialTaskSet):
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
        response = self.client.get(url, headers=headers, name="CI_VIEW_EXECUTION_START - ")
        return response

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
        response = organization.getOrganizationPermissionByResource(self, self.accountID, "default", self.bearerToken)
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
    def getSourceCodeManager_25(self):
        response = source_code.getSourceCodeManager(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionSummaryAll_26(self):
        response = pipeline.getPipelineExecutionSummaryAll(self, self.accountID, self.orgId, projectId, self.bearerToken)
        json_resp = json.loads(response.content)
        self.pipelineId = json_resp['data']['content'][0]['pipelineIdentifier']
        self.pipelineExecutionId = json_resp['data']['content'][0]['planExecutionId']
        self.buildId = json_resp['data']['content'][0]['runSequence']
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGlobalFreezeWithBannerDetails_27(self):
        response = freeze.getGlobalFreezeWithBannerDetails(self, self.accountID, self.orgId, projectId, self.bearerToken)
        json_resp = json.loads(response.content)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGitSync_28(self):
        response = gitsync.getGitSync(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineListFilter_29(self):
        response = pipeline.getPipelineListFilter(self, self.accountID, self.orgId, projectId, '', self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionListRepos_30(self):
        response = pipeline.getPipelineExecutionListRepo(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelinePermissionByPipelineId_31(self):
        response = pipeline.getPipelinePermissionByPipelineIdEditExecute(self, self.accountID, self.orgId, projectId, self.pipelineId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionSummaryFilter_32(self):
        response = pipeline.getPipelineExecutionSummaryFilter(self, self.accountID, self.orgId, projectId, self.pipelineId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionSummary_33(self):
        response = pipeline.getPipelineExecutionSummary(self, self.accountID, self.orgId, projectId, self.pipelineId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task(2)
    def getAccountDetails_34(self):
        response = account.getAccountDetails(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionRetryHistory_35(self):
        response = pipeline.getPipelineExecutionRetryHistory(self, self.accountID, self.orgId, projectId, self.pipelineId, self.pipelineExecutionId,
                                                        self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTiServiceToken_36(self):
        response = ti.getTiServiceToken(self, self.accountID, self.bearerToken)
        self.tiServiceToken = response.content
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getProjectAggregateAll_37(self):
        response = project.getProjectList(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineViewPermission_38(self):
        response = pipeline.getPipelinePermissionById(self, self.accountID, self.orgId, projectId, self.pipelineId, "core_pipeline_view", self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineExecutionV2_39(self):
        response = pipeline.getPipelineExecutionV2(self, self.accountID, self.orgId, projectId, self.pipelineExecutionId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getDeprecatedConfig_CI_40(self):
        response = pipeline.getDeprecatedConfig(self, self.accountID, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getGitSync_41(self):
        response = gitsync.getGitSync(self, self.accountID, self.orgId, projectId, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getTiServiceReportSummary_42(self):
        response = ti.getTiServiceReportSummary(self, self.accountID, self.orgId, projectId, self.pipelineId, self.buildId,
                                                self.tiServiceToken, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getLogServiceToken_43(self):
        response = log_service.getLogServiceToken(self, self.accountID, self.bearerToken)
        self.logServiceToken = response.content
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getLogServiceStream_44(self):
        response = log_service.getLogServiceStream(self, self.accountID, self.orgId, projectId, self.pipelineId,
                                                   self.logServiceToken, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    # @task
    # Disabled due to customized parameters
    # And it does not get called on running build and we pick latest pipeline on list
    def getLogServiceBlob_45(self):
        response = log_service.getLogServiceBlob(self, self.accountID, self.orgId, projectId, self.pipelineId, self.logServiceToken, self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def checkPoint_end(self):
        headers = {'Content-Type': 'application/json'}
        url = "/api/version"
        response = self.client.get(url, headers=headers, name="CI_VIEW_EXECUTION_END - ")
        return response
