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

def entities(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'entities'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("entities", entities)
    
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
            global entity_count_needed
            entity_count_needed = environment.parsed_options.pipeline_execution_count
            global entity_count
            entity_count = 0
            env = environment.parsed_options.env

            utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))

            global accountId
            global uniqueId
            global orgId
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
            json_response = authentication.getAccountInfo(hostname, base64UsernamePassword, auth_mechanism)
            bearerToken = json_response['resource']['token']
            accountId = json_response['resource']['defaultAccountId']

            # get repo url and repo name
            repoUrl = variable.getVariableValue(hostname, accountId, '', '', 'repoUrl', bearerToken)
            repoName = re.search(r'/([^/]+?)(?:\.git)?$', repoUrl).group(1)

            # get k8s namespace
            namespace = variable.getVariableValue(hostname, accountId, '', '', 'k8sNamespace', bearerToken)

            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                global uniqueId
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("entities", uniqueId)
                print("GENERATING TEST DATA ON ENTITIES WITH UNIQUE ID - " + uniqueId)
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
                connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, githubConnId,
                                                          repoUrl, 'account.user0',
                                                          'account.token0',
                                                          bearerToken)
    except Exception:
        logging.exception("Exception occurred while generating test data for ENTITIES")
        utils.stopLocustTests()

def create_pipeline_template(hostname, identifier, versionId, accountID, orgId, projectId, connectorRef, bearerToken):
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
    url = "/template/api/templates?accountIdentifier=" + accountID + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&comments=&isNewTemplate=true&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    if response.status_code != 200:
        print("Pipeline template created as part of test data failed")
        print(response.url)
        print(response.content)

def create_ci_pipeline(hostname, identifier, accountID, orgId, projectId, githubConnId, k8sConnId, dockerConnId, templateId, templateVersionId, namespace, bearerToken):
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
        "namespace": namespace
    }
    url = "/pipeline/api/pipelines/v2?accountIdentifier=" + accountID + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken, "CREATE CI PIPELINE")
    if response.status_code != 200:
        print("Pipeline created as part of test data failed")
        print(response.url)
        print(response.content)
    return response

class ORGANIZATION(SequentialTaskSet):
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
    def executionChecker(self):
        global entity_count
        if entity_count >= entity_count_needed:
            print('Entity Count Reached, hence its Perf test is gonna be stopped')
            headers = {'Connection': 'keep-alive'}
            stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
            if stopResponse.status_code == 200:
                print('Perf Test has been stopped')
                self.interrupt()
            else:
                print('Alarm Perf Tests are still running')
                print(stopResponse.content)

    @task
    def createRandomString(self):
        self.randomString = ''.join(choice(ascii_lowercase) for i in range(4))

    @task
    def createOrganization(self):
        global entity_count
        orgId = "org_e_"+utils.getUniqueString()
        print(orgId)
        if entity_count < entity_count_needed:
            print("ORGANIZATION COUNT - " + str(entity_count))
            response = organization.createOrg(self, orgId, self.accountId, self.bearerToken)

            if response.status_code == 200:
                entity_count += 1
                if entity_count >= entity_count_needed:
                    print('Entity Count Reached, hence its Perf test is gonna be stopped')
                    headers = {'Connection': 'keep-alive'}
                    stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
                    if stopResponse.status_code == 200:
                        print('Perf Test has been stopped')
                        self.interrupt()
                    else:
                        print('Alarm Perf Tests are still running')
                        print(stopResponse.content)
            else:
                print("Entity creation failure with status code : "+response.status_code)
                utils.print_error_log(response)

class PROJECT(SequentialTaskSet):
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
        self.authentication()

    @task
    def executionChecker(self):
        global entity_count
        global locust_server_url
        if entity_count >= entity_count_needed:
            print('Entity Count Reached, hence its Perf test is gonna be stopped')
            headers = {'Connection': 'keep-alive'}
            stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
            if stopResponse.status_code == 200:
                print('Perf Test has been stopped')
                self.interrupt()
            else:
                print('Alarm Perf Tests are still running')
                print(stopResponse.content)

    @task
    def createRandomString(self):
        self.randomString = ''.join(choice(ascii_lowercase) for i in range(4))

    @task
    def createProject(self):
        global entity_count
        orgId = "org_for_perf_project";
        projectId = "project_e_"+utils.getUniqueString()
        print(projectId)
        if entity_count < entity_count_needed:
            print("PROJECT COUNT - "+str(entity_count))
            response = project.createProject(self, projectId, orgId, self.accountId, self.bearerToken)

            if response.status_code == 200:
                entity_count += 1
                if entity_count >= entity_count_needed:
                    print('Entity Count Reached, hence its Perf test is gonna be stopped')
                    headers = {'Connection': 'keep-alive'}
                    stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
                    if stopResponse.status_code == 200:
                        print('Perf Test has been stopped')
                        self.interrupt()
                    else:
                        print('Alarm Perf Tests are still running')
                        print(stopResponse.content)
            else:
                print("Entity creation failure with status code : "+response.status_code)
                utils.print_error_log(response)

class PIPELINE(SequentialTaskSet):

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
        self.authentication()

    @task
    def executionChecker(self):
        global entity_count
        global locust_server_url
        if entity_count >= entity_count_needed:
            print('Entity Count Reached, hence its Perf test is gonna be stopped')
            headers = {'Connection': 'keep-alive'}
            stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
            if stopResponse.status_code == 200:
                print('Perf Test has been stopped')
                self.interrupt()
            else:
                print('Alarm Perf Tests are still running')
                print(stopResponse.content)

    @task
    def createRandomString(self):
        self.randomString = ''.join(choice(ascii_lowercase) for i in range(4))

    @task
    def createPipeline(self):
        global entity_count
        orgId = "auto_org_" + uniqueId
        pipelineId = "perf_pipeline_"+utils.getUniqueString()
        print("creating {} in {} with count {}".format(pipelineId, orgId, str(entity_count)))
        if entity_count < entity_count_needed:
            response = create_ci_pipeline(self, pipelineId, self.accountId, orgId, projectId, githubConnId, k8sConnId, dockerConnId, templateId, templateVersionId, namespace, self.bearerToken)

            if response.status_code == 200:
                entity_count += 1
                if entity_count >= entity_count_needed:
                    print('Entity Count Reached, hence its Perf test is gonna be stopped')
                    headers = {'Connection': 'keep-alive'}
                    stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
                    if stopResponse.status_code == 200:
                        print('Perf Test has been stopped')
                        self.interrupt()
                    else:
                        print('Alarm Perf Tests are still running')
                        print(stopResponse.content)
            else:
                print("Entity creation failure with status code : "+response.status_code)
                utils.print_error_log(response)
