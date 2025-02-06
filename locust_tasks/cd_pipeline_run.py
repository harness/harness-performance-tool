import base64
import json
import logging
import random
import sys
import time

import gevent
import yaml
import requests
from locust import task, constant_pacing, SequentialTaskSet, events
from locust.exception import StopUser
from locust.runners import LocalRunner, MasterRunner, STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP
from locust.runners import WorkerRunner

from locust_tasks.helpers import authentication
from locust_tasks.helpers.ng import helpers
from locust_tasks.helpers.ng import organization, project, connector, pipeline, service, infra, variable, \
    en as envHelper

from utilities import utils
from utilities.utils import getPath, CSVReader

uniqueId = None


def checker(environment):
    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > 0.2:
            print(f"fail ratio was {environment.runner.stats.total.fail_ratio}, quitting")
            environment.runner.quit()
            return


def cd_pipeline_run(environment, msg, **kwargs):
    global uniqueId
    uniqueId = msg.data


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("cd_pipeline_run", cd_pipeline_run)


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

        if testdata_setup:
            global hostname
            hostname = environment.host
            global deployment_count_needed
            deployment_count_needed = environment.parsed_options.pipeline_execution_count
            global deployment_count
            deployment_count = 0
            env = environment.parsed_options.env

            utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))

            global uniqueId
            global accountId
            global orgId
            global projectId
            global awsSecretKeyId
            global awsAccessKeyId
            global awsConnId
            global serviceId
            global envId
            global infraId
            global k8sConnId
            global delegate_tag
            delegate_tag = 'perf-delegate'

            global awsRegion
            global awsArtifactImage
            global awsArtifactTag
            global manifestRepoUrl
            global manifestRepoCommitId
            global pipeline_count
            pipeline_count = 1

            projectId = "perf_project"
            awsSecretKeyId = "account.awssecretkey"  # secret should be present already on account level
            awsAccessKeyId = "account.awsaccesskey"  # secret should be present already on account level
            awsConnId = "perf_conn_aws"
            k8sConnId = "perf_conn_k8s"
            envId = "perf_env_k8s"
            serviceId = "perf_svc_k8s"
            infraId = "perf_infra_k8s"

            username_list = CSVReader(getPath('data/{}/credentials.csv'.format(env)))
            creds = next(username_list)[0].split(':')
            c = creds[0] + ':' + creds[1]
            en = base64.b64encode(c.encode('ascii'))
            base64UsernamePassword = 'Basic ' + en.decode('ascii')
            json_response = authentication.getAccountInfo(hostname, base64UsernamePassword, auth_mechanism)
            bearerToken = json_response['resource']['token']
            accountId = json_response['resource']['defaultAccountId']

            # executing on master to avoid running on multiple workers
            if isinstance(environment.runner, MasterRunner) | isinstance(environment.runner, LocalRunner):
                global uniqueId
                uniqueId = utils.getUniqueString()
                environment.runner.send_message("cd_pipeline_run", uniqueId)
                print(f"Generating test data for CD_PIPELINE_RUN with ID {uniqueId}")
                orgId = "auto_cd_k8s_org_" + uniqueId
                organization.createOrg(hostname, orgId, accountId, bearerToken)
                project.createProject(hostname, projectId, orgId, accountId, bearerToken)

                manifestRepoUrl = get_account_variable(hostname, bearerToken, accountId, 'manifestRepoUrl')
                manifestRepoCommitId = get_account_variable(hostname, bearerToken, accountId,
                                                            'manifestRepoCommitId')
                awsRegion = get_account_variable(hostname, bearerToken, accountId, 'awsRegion')
                awsArtifactImage = get_account_variable(hostname, bearerToken, accountId, 'awsArtifactImage')
                awsArtifactTag = get_account_variable(hostname, bearerToken, accountId, 'awsArtifactTag')

                connector.createAwsConnector(hostname, bearerToken, accountId, orgId, projectId, awsConnId, awsSecretKeyId,
                                             awsAccessKeyId, awsRegion)
                for index in range(pipeline_count):
                    create_github_connector(hostname, bearerToken, accountId, orgId, projectId, manifestRepoUrl, index)

                response = service.createK8sSvcWithRuntimeGHConnectorAndEcrConnector(hostname, accountId, orgId, projectId,
                                                                                     bearerToken, serviceId,
                                                                                     manifestRepoCommitId,
                                                                                     awsConnId, awsArtifactImage,
                                                                                     awsArtifactTag,
                                                                                     awsRegion)
                log_response(response, 'INIT:CREATE_SERVICE')

                response = envHelper.createEnvironment(hostname, accountId, orgId, projectId, envId, bearerToken)
                log_response(response, 'INIT:CREATE_ENV')

                response = connector.createK8sConnector_delegate(hostname, accountId, orgId, projectId, k8sConnId, delegate_tag, bearerToken)
                log_response(response, 'INIT:CREATE_CONNECTOR')

                response = infra.createK8sDirectInfra(hostname, accountId, orgId, projectId, infraId, envId, k8sConnId,
                                                      bearerToken)
                log_response(response, 'INIT:CREATE_INFRA')

                pipeline_id = "perf_pipeline_" + uniqueId + "0"
                response = create_k8s_pipeline(hostname, accountId, orgId, projectId, pipeline_id, serviceId, envId,
                                               infraId,
                                               delegate_tag, bearerToken)
                log_response(response, 'INIT:CREATE_PIPELINE')
    except Exception:
        logging.exception("Exception occurred while generating test data for CD_PIPELINE_RUN")
        utils.stopLocustTests()


def create_github_connector(hostname, bearerToken, accountId, orgId, projectId, manifestRepoUrl, index):
    connector_id = 'perf_github_connector_' + str(index)
    connector.createGithubConnectorViaUserRef(hostname, accountId, orgId, projectId, connector_id,
                                              manifestRepoUrl, 'account.user' + str(index),
                                              'account.token' + str(index),
                                              bearerToken)


def get_account_variable(hostname, bearerToken, accountId, key):
    varResponse = variable.getVariableDetails(hostname, accountId, '', '', key, bearerToken)
    json_resp = json.loads(varResponse.content)
    return str(json_resp['data']['variable']['spec']['fixedValue'])


def log_response(response, action):
    if response.status_code != 200:
        logging.error(f"Failed to perform action {action} with status code {response.status_code}")
        utils.log_error_response(response)
    else:
        logging.info(f"Successfully performed action {action}")


def create_k8s_pipeline(hostname, accountId, orgId, projectId, pipeline_id, serviceId, envId, infraId,
                        delegate_selector, bearerToken):
    with open(getPath('resources/NG/pipeline/cd/pipeline_cd_k8s_canary.yaml'), 'r+') as f:
        # Updating the Json File
        pipelineData = yaml.load(f, Loader=yaml.FullLoader)
        payload = str(yaml.dump(pipelineData, default_flow_style=False))
        f.truncate()
    dataMap = {
        "identifier": pipeline_id,
        "orgIdentifier": orgId,
        "projectIdentifier": projectId,
        "serviceName": serviceId,
        "environmentName": envId,
        "infraName": infraId,
        "delegateSelector": delegate_selector,
    }
    url = "/pipeline/api/pipelines/v2?accountIdentifier=" + accountId + "&projectIdentifier=" + projectId + "&orgIdentifier=" + orgId + "&storeType=INLINE"
    response = pipeline.postPipelineWithYamlPayload(hostname, payload, dataMap, url, bearerToken)
    return response


class CD_PIPELINE_RUN(SequentialTaskSet):
    def data_initiator(self):
        self.__class__.wait_time = constant_pacing(1)

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
        self.orgId = "auto_cd_k8s_org_" + uniqueId

    @task
    def trigger_pipeline(self):
        global deployment_count
        deployment_count += 1
        if deployment_count <= deployment_count_needed:
            id = "perf_pipeline_" + uniqueId + str(random.randint(0, (pipeline_count-1)))
            with open(getPath('resources/NG/pipeline/inputs_cd_k8s_canary_payload.yaml'), 'r+') as f:
                # Updating the Json File
                pipelineData = yaml.load(f, Loader=yaml.FullLoader)
                payload = str(yaml.dump(pipelineData, default_flow_style=False))
                f.truncate()
            github_random_connector = "perf_github_connector_" + str(random.randint(0, (pipeline_count-1)))
            dataMap = {
                "pipelineId": id,
                "manifestConnectorRef": github_random_connector
            }
            if dataMap is not None:
                for key in dataMap:
                    if key is not None:
                        payload = payload.replace('$' + key, dataMap[key])
            response = helpers.triggerPipeline(self, id, projectId, self.orgId, "cd",
                                               self.accountId, self.bearerToken, payload)

            if response.status_code == 200:
                logging.info('Pipeline is triggered successfully ')
                if deployment_count >= deployment_count_needed:
                    logging.info('Deployment Count Reached, hence its Perf test is gonna be stopped')
                    headers = {'Connection': 'keep-alive'}
                    stopResponse = requests.get(utils.getLocustMasterUrl() + '/stop', headers=headers)
                    if stopResponse.status_code == 200:
                        print('Perf Test has been stopped')
                        self.interrupt()
                    else:
                        print('Alarm Perf Tests are still running')
                        print(stopResponse.content)
            else:
                utils.log_error_response(response)
