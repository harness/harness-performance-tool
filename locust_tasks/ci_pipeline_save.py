import sys
import time
import gevent
import requests
import yaml
import base64
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

def ci_pipeline_save(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'ci_pipeline_save'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("ci_pipeline_save", ci_pipeline_save)

@events.test_start.add_listener
def initiator(environment, **kwargs):
    testdata_setup = False
    arr = utils.getTestClasses(environment)
    for ar in arr:
        try:
            ar = ar.replace('_CLASS', '') if '_CLASS' in ar else ar
            getattr(sys.modules[__name__], ar)
            testdata_setup = True
        except Exception:
            pass

    if testdata_setup == True:
        global hostname
        hostname = environment.host
        global intList
        global intListIter
        env = environment.parsed_options.env

        utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))
        intList = list(range(0, 15)) #0,15
        intListIter = iter(intList)

        # pre-requisite
        # create org, project, secret, gitConn, dockerConn, template

        global uniqueId
        global accountId
        global orgId
        global projectId
        projectId = "perf_project"
        global dockerConnId
        dockerConnId = "perf_conn_docker"
        global stepTemplateId
        stepTemplateId = "perf_step_template"
        global templateVersionId
        templateVersionId = "version1"
        global k8sConnId
        k8sConnId = "perf_conn_k8s_del"
        global namespace
        namespace = 'default'
        global delegate_tag
        delegate_tag = 'perf-delegate'
        global repoUrl
        global githubConnId
        githubConnId = "perf_conn_github_"
        # eg: "perf_conn_github_" + uniqueId + 1

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
            environment.runner.send_message("ci_pipeline_save", uniqueId)
            print("GENERATING TEST DATA ON CI_PIPELINE_SAVE WITH UNIQUE ID - " + uniqueId)
            orgId = "auto_org_" + uniqueId
            organization.createOrg(hostname, orgId, accountId, bearerToken)
            project.createProject(hostname, projectId, orgId, accountId, bearerToken)
            connector.createDockerConnectorAnonymous(hostname, accountId, orgId, projectId, dockerConnId,
                                                         'https://index.docker.io/v2/', bearerToken)
            connector.createK8sConnector_delegate(hostname, accountId, orgId, projectId, k8sConnId, delegate_tag, bearerToken)
            varResponse = variable.getVariableDetails(hostname, accountId, '', '', 'repoUrl', bearerToken)
            json_resp = json.loads(varResponse.content)
            repoUrl = str(json_resp['data']['variable']['spec']['fixedValue'])
            create_pipeline_template(hostname, stepTemplateId, templateVersionId, accountId, orgId, projectId, dockerConnId,
                                     bearerToken)
            def setup_data(index):
                # use existing harness secret eg: user0 (repo userid) | token0 (repo user token)
                github_conn_id = githubConnId +uniqueId+str(index)
                connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, github_conn_id, repoUrl,
                                                        'account.user' + str(index), 'account.token' + str(index), bearerToken)

            github_conn_count = len(intList)
            for index in range(github_conn_count):
                setup_data(index)

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


# create new pipeline and update (non-git)
class CI_PIPELINE_SAVE(SequentialTaskSet):
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

    def getIndex(self):
        global intListIter
        try:
            index = next(intListIter)
        except StopIteration:
            intListIter = iter(intList)
            index = next(intListIter)
        return index

    def on_start(self):
        self.data_initiator()
        self.authentication()

    @task
    def setup_data(self):
        self.index = self.getIndex()
        self.orgId = "auto_org_" + uniqueId
        self.pipelineId = "perf_pipeline_" + utils.getUniqueString()
        self.github_conn_id = githubConnId + uniqueId + str(self.index)

    @task
    def createCIPipeline_1(self):
        print("----CREATE ID--"+self.pipelineId)
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_infra_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef": self.github_conn_id,
            "dockerConnectorRef": dockerConnId,
            "templateRef": stepTemplateId,
            "versionLabel": templateVersionId,
            "k8sConnectorRef": k8sConnId,
            "namespace": namespace
        }
        url = "/pipeline/api/pipelines/v2?accountIdentifier=" + self.accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + self.orgId + "&storeType=INLINE"
        response = pipeline.postPipelineWithYamlPayload(self, payload, dataMap, url, self.bearerToken, "CREATE CI PIPELINE - ")
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def getPipelineDetails_2(self):
        print("----GET ID--" + self.pipelineId)
        response = pipeline.getPipelineDetails1(self, self.accountId, self.orgId, projectId, self.pipelineId,
                                                self.bearerToken)
        if response.status_code != 200:
            utils.print_error_log(response)

    @task
    def updateCIPipeline_3(self):
        print("----UPDATE ID--" + self.pipelineId)
        with open(getPath('resources/NG/pipeline/ci/pipeline_step1_step2_step3_infra_payload.yaml'), 'r+') as f:
            # Updating the Json File
            pipelineData = yaml.load(f, Loader=yaml.FullLoader)
            payload = str(yaml.dump(pipelineData, default_flow_style=False))
            f.truncate()
        dataMap = {
            "identifier": self.pipelineId,
            "orgIdentifier": self.orgId,
            "projectIdentifier": projectId,
            "gitConnectorRef": self.github_conn_id,
            "dockerConnectorRef": dockerConnId,
            "templateRef": stepTemplateId,
            "versionLabel": templateVersionId,
            "k8sConnectorRef": k8sConnId,
            "namespace": namespace
        }
        url = "/pipeline/api/pipelines/v2/"+self.pipelineId+"?accountIdentifier=" + self.accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + self.orgId
        response = pipeline.putPipelineWithYamlPayload(self, payload, dataMap, url, self.bearerToken,
                                                        "UPDATE CI PIPELINE - ")
        if response.status_code != 200:
            utils.print_error_log(response)
