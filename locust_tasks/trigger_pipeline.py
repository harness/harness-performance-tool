
import base64
import json
import sys
import time
import gevent
import requests
import logging
from random import choice
from string import ascii_lowercase
from locust.exception import StopUser
from locust_tasks.utilities import utils
from utilities.utils import getPath
from locust.runners import LocalRunner, MasterRunner, WorkerRunner, STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP
from locust_tasks.helpers.ng import helpers
from locust import task, SequentialTaskSet, events


def checker(environment):
    while not environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        time.sleep(1)
        if environment.runner.stats.total.fail_ratio > 0.2:
            print(f"fail ratio was {environment.runner.stats.total.fail_ratio}, quitting")
            environment.runner.quit()
            return

def trigger_pipeline(environment, msg, **kwargs):
    # Fired when the worker receives a message of type 'trigger_pipeline'
    global uniqueId
    uniqueId = msg.data

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    if not isinstance(environment.runner, WorkerRunner):
        gevent.spawn(checker, environment)
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("trigger_pipeline", trigger_pipeline)

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
            global uniqueId
            uniqueId = "" # uniqueId required to run pipeline with webhook (mandatory)
            environment.runner.send_message("trigger_pipeline", uniqueId)
            global deployment_count_needed
            deployment_count_needed = environment.parsed_options.pipeline_execution_count
            global deployment_count
            deployment_count = 0
            global pipeline_link
            pipeline_link = environment.parsed_options.pipeline_url
            global env
            env = environment.parsed_options.env

            utils.init_userid_file(getPath('data/{}/credentials.csv'.format(env)))
    except Exception:
        logging.exception("Exception occurred while generating test data for TRIGGER_PIPELINE")
        utils.stopLocustTests()

class TRIGGER_PIPELINE(SequentialTaskSet):

    def data_initiator(self):
        self.pipeline_comps = pipeline_link.split('/')

        if '/api/webhook' not in pipeline_link:
            self.orgName = self.pipeline_comps[8]
            self.projectName = self.pipeline_comps[10]
            self.pipelineIdentifier = self.pipeline_comps[12]
            self.moduleName = self.pipeline_comps[6]

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
    def createRandomString(self):
        self.randomString = ''.join(choice(ascii_lowercase) for i in range(3))

    @task
    def triggerPipeline(self):
        global deployment_count
        deployment_count += 1
        if deployment_count <= deployment_count_needed:
            if '/api/webhook' not in pipeline_link:
                response = helpers.triggerPipelineWithoutPayload(self, self.pipelineIdentifier, self.projectName,
                                                                   self.orgName,
                                                                   self.moduleName, self.accountId, self.bearerToken)
            else:
                response = helpers.triggerWithWebHook(self, self.accountId, uniqueId)

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

