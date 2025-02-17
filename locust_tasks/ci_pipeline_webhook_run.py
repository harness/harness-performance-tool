import re
import sys
import time
import gevent
import requests
import yaml
import base64
import logging
import random
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
            utils.stopLocustTests()
            return

def ci_pipeline_webhook_run(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'ci_pipeline_webhook_run'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("ci_pipeline_webhook_run", ci_pipeline_webhook_run)

@events.test_start.add_listener
def initiator(environment, **kwargs):
    environment.runner.state = "TESTDATA SETUP"
    global auth_mechanism
    auth_mechanism = environment.parsed_options.auth_mechanism
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
            # create org, project, secret, gitConn, dockerConn, template, pipeline (non-git)

            global uniqueId
            global accountId
            global orgId
            global projectId
            projectId = "perf_project"
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
            global repoBranchName

            # generate bearer token for test data setup
            username_list = CSVReader(getPath('data/{}/credentials.csv'.format(env)))
            creds = next(username_list)[0].split(':')
            c = creds[0] + ':' + creds[1]
            en = base64.b64encode(c.encode('ascii'))
            base64UsernamePassword = 'Basic ' + en.decode('ascii')
            json_response = authentication.getAccountInfo(hostname, base64UsernamePassword, auth_mechanism)
            bearerToken = json_response['resource']['token']
            accountId = json_response['resource']['defaultAccountId']

            # get repo url and repo name
            repoUrl = variable.getVariableValue(hostname, accountId, '', '', 'repoUrl', bearerToken)
            repoName = re.search(r'/([^/]+?)(?:\.git)?$', repoUrl).group(1)

            # get repo branch name
            repoBranchName = variable.getVariableValue(hostname, accountId, '', '', 'repoBranchName', bearerToken)

            # get k8s namespace
            namespace = variable.getVariableValue(hostname, accountId, '', '', 'k8sNamespace', bearerToken)

            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                global uniqueId
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("ci_pipeline_webhook_run", uniqueId)
                print("GENERATING TEST DATA ON ci_pipeline_webhook_run WITH UNIQUE ID - " + uniqueId)
                orgId = "auto_org_" + uniqueId
                organization.createOrg(hostname, orgId, accountId, bearerToken)
                project.createProject(hostname, projectId, orgId, accountId, bearerToken)
                connector.createDockerConnectorAnonymous(hostname, accountId, orgId, projectId, dockerConnId,
                                                             'https://index.docker.io/v2/', bearerToken)
                create_pipeline_template(hostname, templateId, templateVersionId, accountId, orgId, projectId, dockerConnId,
                                         bearerToken)
                connector.createK8sConnector_delegate(hostname, accountId, orgId, projectId, k8sConnId, delegate_tag, bearerToken)
                def setup_data(index):
                    # use existing harness secret eg: user0 (repo userid) | token0 (repo user token)
                    githubConnId = "perf_conn_github_" + uniqueId + str(index)
                    connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, githubConnId,
                                                    repoUrl, 'account.user'+str(index), 'account.token'+str(index), bearerToken)
                    pipelineId = "perf_pipeline_"+uniqueId+str(index)
                    delegate_selected = delegate_tag
                    create_ci_pipeline(hostname, pipelineId, accountId, orgId, projectId, githubConnId, k8sConnId, dockerConnId,
                                       templateId, templateVersionId, namespace, delegate_selected, bearerToken)
                    inputSetId = "perf_inputset_" + uniqueId + str(index)
                    create_ci_inputset(hostname, inputSetId, accountId, orgId, projectId, pipelineId, delegate_selected, bearerToken)
                    triggerId = "perf_trigger_remote_" + uniqueId + str(index)
                    create_ci_trigger_remote(hostname, triggerId, accountId, orgId, projectId, githubConnId, pipelineId, inputSetId, delegate_selected, bearerToken)

                pipeline_count = 15
                for index in range(pipeline_count):
                    setup_data(index)
    except Exception:
        logging.exception("Exception occurred while generating test data for ci_pipeline_webhook_run")
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

def create_ci_pipeline(hostname, identifier, accountId, orgId, projectId, githubConnId, k8sConnId, dockerConnId, templateId, templateVersionId, namespace, delegate, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "gitConnectorRef": githubConnId,
        "dockerConnectorRef": dockerConnId,
        "templateRef": templateId,
        "versionLabel": templateVersionId,
        "k8sConnectorRef": k8sConnId,
        "namespace": namespace,
        "delegate": delegate
    }
    url = "/pipeline/api/pipelines/v2?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline created as part of test data failed")
        utils.print_error_log(response)

def create_ci_inputset(hostname, identifier, accountId, orgId, projectId, pipelineIdentifier, delegate, bearerToken):
    with open(getPath('resources/NG/pipeline/ci/inputset_remote.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": identifier,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "pipelineIdentifier": pipelineIdentifier,
        "branch": repoBranchName,
        "delegate": delegate
    }
    url = "/pipeline/api/inputSets?routingId=" + accountId +"&accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&pipelineIdentifier=" + pipelineIdentifier + "&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline input set created as part of test data failed")
        utils.print_error_log(response)

def create_ci_trigger_remote(hostname, identifier, accountId, orgId, projectId, githubConnId, pipelineIdentifier, inputSetId, delegate, bearerToken):
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
        "payloadConditionValue": uniqueId,
        "branch": repoBranchName,
        "delegate": delegate
    }
    url = "/pipeline/api/triggers?routingId=" + accountId +"&accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&targetIdentifier=" + pipelineIdentifier + \
          "&ignoreError=false&branch="+repoBranchName+"&connectorRef=" + githubConnId + "&repoName="+repoName+"&storeType=REMOTE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline trigger created as part of test data failed")
        utils.print_error_log(response)

# Trigger non-git pipeline added above 'deployment_count_needed' times
class CI_PIPELINE_WEBHOOK_RUN(SequentialTaskSet):
    def data_initiator(self):
        self.__class__.wait_time = constant_pacing(1 // 1)

    def authentication(self):
        creds = next(utils.userid_list)[0].split(':')
        c = creds[0] + ":" + creds[1]
        en = base64.b64encode(c.encode('ascii'))
        payload = {"authorization": 'Basic ' + en.decode('ascii')}
        headers = {'Content-Type': 'application/json'}
        uri = '/api/users/login'
        if auth_mechanism.lower() == "local-login":
            uri = '/gateway/api/users/harness-local-login'
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
        self.authentication()

    @task
    def setup_data(self):
        self.orgId = "auto_org_" + uniqueId

    @task
    def triggerPipeline(self):
        global deployment_count
        deployment_count += 1
        if deployment_count <= deployment_count_needed:
            response = helpers.triggerWithWebHook(self, accountId, uniqueId)

            if response.status_code == 200:
                print('Pipeline is triggered successfully ')
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
