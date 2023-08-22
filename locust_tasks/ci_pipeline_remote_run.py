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
from locust_tasks.helpers.ng import helpers
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

def ci_pipeline_remote_run(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'ci_pipeline_remote_run'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("ci_pipeline_remote_run", ci_pipeline_remote_run)

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
            global deployment_count_needed
            deployment_count_needed = environment.parsed_options.pipeline_execution_count
            global deployment_count
            deployment_count = 0
            env = environment.parsed_options.env

            utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))

            # pre-requisite
            # create org, project, secret, gitConn, dockerConn, template (stage & step remote), pipeline (remote)
            # input set (remote), trigger

            global uniqueId
            global accountId
            global orgId
            global projectId
            projectId = "perf_project"
            global dockerConnId
            dockerConnId = "perf_conn_docker"
            global templateId
            global templateVersionId
            global k8sConnId
            k8sConnId = "perf_conn_k8s_del"
            global namespace
            namespace = 'default'
            global delegate_tag
            delegate_tag = 'perf-delegate'
            global repoUrl

            # generate bearer token for test data setup
            username_list = CSVReader(getPath('data/{}/credentials.csv'.format(env)))
            creds = next(username_list)[0].split(':')
            c = creds[0] + ':' + creds[1]
            en = base64.b64encode(c.encode('ascii'))
            base64UsernamePassword = 'Basic ' + en.decode('ascii')
            json_response = authentication.getAccountInfo(hostname, base64UsernamePassword)
            bearerToken = json_response['resource']['token']
            accountId = json_response['resource']['defaultAccountId']

            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("ci_pipeline_remote_run", uniqueId)
                print("GENERATING TEST DATA ON CI_PIPELINE_REMOTE_RUN WITH UNIQUE ID - " + uniqueId)
                orgId = "auto_org_" + uniqueId
                organization.createOrg(hostname, orgId, accountId, bearerToken)
                project.createProject(hostname, projectId, orgId, accountId, bearerToken)
                connector.createDockerConnectorAnonymous(hostname, accountId, orgId, projectId, dockerConnId,
                                                             'https://index.docker.io/v2/', bearerToken)
                connector.createK8sConnector_delegate(hostname, accountId, orgId, projectId, k8sConnId, delegate_tag, bearerToken)
                varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'repoUrl', bearerToken)
                json_resp = json.loads(varResponse.content)
                repoUrl = str(json_resp['data']['variable']['spec']['fixedValue'])
                def setup_data(index):
                    # use existing harness secret eg: user0 (repo userid) | token0 (repo user token)
                    githubConnId = "perf_conn_github_" + uniqueId + str(index)
                    connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, githubConnId, repoUrl,
                                                              'account.user' + str(index), 'account.token' + str(index), bearerToken)
                    step_templateId = "perf_step_template_"+uniqueId+str(index)
                    step_templateVersionId = "version1"
                    create_pipeline_step_template(hostname, step_templateId, step_templateVersionId, accountId, orgId, projectId,
                                                  dockerConnId, githubConnId, bearerToken)
                    time.sleep(2)
                    stage_templateId = "perf_stage_template_" + uniqueId + str(index)
                    stage_templateVersionId = "version1"
                    create_pipeline_stage_template(hostname, stage_templateId, stage_templateVersionId, accountId, orgId, projectId,
                                                  k8sConnId, githubConnId, step_templateId, step_templateVersionId, bearerToken)
                    time.sleep(2)
                    pipelineId = "perf_pipeline_remote_"+uniqueId+str(index)
                    create_ci_pipeline_remote(hostname, pipelineId, accountId, orgId, projectId, githubConnId, stage_templateId, stage_templateVersionId, bearerToken)
                    inputSetId = "perf_inputset_remote_" + uniqueId + str(index)
                    create_ci_inputset_remote(hostname, inputSetId, accountId, orgId, projectId, githubConnId, pipelineId, bearerToken)
                    triggerId = "perf_trigger_remote_" + uniqueId + str(index)
                    create_ci_trigger_remote(hostname, triggerId, accountId, orgId, projectId, githubConnId, pipelineId, inputSetId, bearerToken)

                pipeline_count = 15
                for index in range(pipeline_count):
                    setup_data(index)
    except Exception:
        logging.exception("Exception occurred while generating test data for CI_PIPELINE_REMOTE_RUN")
        utils.stopLocustTests()

def create_pipeline_step_template(hostname, identifier, versionId, accountId, orgId, projectId, connectorRef, githubConnId, bearerToken):
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
        "parallelism": "5"
    }
    url = "/template/api/templates?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&comments=&commitMsg="+ identifier +"&createPr=false&isNewBranch=false&branch=master&storeType=REMOTE&connectorRef="+ githubConnId +"&repoName=springboot&filePath=.harness%2F"+identifier+".yaml"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline step template created as part of test data failed")
        utils.print_error_log(response)

def create_pipeline_stage_template(hostname, identifier, versionId, accountId, orgId, projectId, connectorRef, githubConnId, stepTemplateRef, stepVersionLabel, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/stage_template_payload.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "versionLabel": versionId,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "connectorRef": connectorRef,
        "namespace": namespace,
        "stepTemplateRef": stepTemplateRef,
        "stepVersionLabel": stepVersionLabel
    }
    url = "/template/api/templates?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&comments=&commitMsg="+ identifier +"&createPr=false&isNewBranch=false&branch=master&storeType=REMOTE&connectorRef="+ githubConnId +"&repoName=springboot&filePath=.harness%2F"+ identifier +".yaml"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline stage template created as part of test data failed")
        utils.print_error_log(response)

def create_ci_pipeline_remote(hostname, identifier, accountId, orgId, projectId, githubConnId, stageTemplateId, stageVersionId, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/pipeline_stage_template_remote_payload.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "gitConnectorRef": githubConnId,
        "stageTemplateRef": stageTemplateId,
        "stageVersionLabel": stageVersionId
    }
    url = "/pipeline/api/pipelines/v2?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&storeType=REMOTE" \
          + "&connectorRef=" + githubConnId + "&commitMsg=" + identifier + "&createPr=false&isNewBranch=false&branch=master&repoName=springboot&filePath=.harness%2F" + identifier + ".yaml"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline created as part of test data failed")
        utils.print_error_log(response)

def create_ci_inputset_remote(hostname, identifier, accountId, orgId, projectId, githubConnId, pipelineIdentifier, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/inputset_remote.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "pipelineIdentifier": pipelineIdentifier
    }
    url = "/pipeline/api/inputSets?routingId=" + accountId +"&accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&pipelineIdentifier=" + pipelineIdentifier \
            + "&pipelineBranch=master&connectorRef="+githubConnId+"&repoName=springboot&branch=master&filePath=.harness%2F"+identifier+".yaml&storeType=REMOTE&commitMsg="+identifier+"&createPr=false&isNewBranch=false"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline input set created as part of test data failed")
        utils.print_error_log(response)

def create_ci_trigger_remote(hostname, identifier, accountId, orgId, projectId, githubConnId, pipelineIdentifier, inputSetId, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/trigger_remote.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "pipelineIdentifier": pipelineIdentifier,
        "connectorRef": githubConnId,
        "inputSetRefs": inputSetId,
        "payloadConditionValue": uniqueId
    }
    url = "/pipeline/api/triggers?routingId=" + accountId +"&accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&targetIdentifier=" + pipelineIdentifier + \
          "&ignoreError=false&branch=master&connectorRef=" + githubConnId + "&repoName=springboot&storeType=REMOTE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline trigger created as part of test data failed")
        utils.print_error_log(response)

# Trigger pipeline added above 'deployment_count_needed' times
class CI_PIPELINE_REMOTE_RUN(SequentialTaskSet):
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
            self.accountId = str(json_resp['resource']['defaultAccountId'])

    def on_start(self):
        self.data_initiator()
        # self.authentication() # CAN BE RUN WITHOUT LOGIN AS WELL

    @task
    def executionChecker(self):
        global deployment_count
        if deployment_count >= deployment_count_needed:
            print('Deployment Count Reached, hence its Perf test is gonna be stopped')
            headers = {'Connection': 'keep-alive'}
            stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
            if stopResponse.status_code == 200:
                print('Perf Test has been stopped')
                self.interrupt()
            else:
                print('Alarm Perf Tests are still running')
                print(stopResponse.content)

    @task
    def triggerPipeline(self):
        global deployment_count
        time.sleep(3)
        if deployment_count < deployment_count_needed:
            response = helpers.triggerWithWebHook(self, accountId, uniqueId)

            if response.status_code == 200:
                print('Pipeline is triggered successfully ')
                deployment_count += 1
                if deployment_count >= deployment_count_needed:
                    print('Deployment Count Reached, hence its Perf test is gonna be stopped')
                    headers = {'Connection': 'keep-alive'}
                    stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
                    if stopResponse.status_code == 200:
                        print('Perf Test has been stopped')
                        self.interrupt()
                    else:
                        print('Alarm Perf Tests are still running')
                        print(stopResponse.content)
            else:
                utils.print_error_log(response)
