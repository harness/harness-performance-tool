
## Harness Performance Testing Framework

This document outlines all the necessary details required for:
1. Setting up a performance test tool (Locust - https://locust.io/) to generate load on Harness system
2. Python scripts that emulate actual user scenarios via Harness apis https://apidocs.harness.io/

### Performance Test Results
[Test Report - 06-Oct-2023](./reports/06-Oct'23.md)  
[Test Report - 27-Oct-2023](./reports/27-Oct'23.md)  
[Test Report - 28-Dec-2023](./reports/28-Dec'23.md)  
[Test Report - 31-Jan-2024](./reports/31-Jan'24.md)  
[Test Report - 29-Feb-2024](./reports/29-Feb'24.md)  
[Test Report - 01-Apr-2024](./reports/01-Apr'24.md)  
[Test Report - 30-Apr-2024](./reports/30-Apr'24.md)  
[Test Report - 05-June-2024](./reports/05-June'24.md)  
[Test Report - 08-July-2024](./reports/08-July'24.md)  
[Test Report - 28-Aug-2024](./reports/28-Aug'24.md)  
[Test Report - 08-Jan-2025](./reports/08-Jan'25.md)  

### Quick overview
[locust_setup_run.mov](https://drive.google.com/file/d/1oU9r0_IBOs908D0YmpRUrCzW9EqmR_hV/view)

### [Project structure](#)
- data : contains harness username list
- kubernetes-config : locust master and worker deployment yaml
- locust_tasks : test scripts and api helpers
- resources : request payload files
- locust_tasks > tasks.py : execution starting point and all the test scripts have to be imported here

### [Test data setup](#)

#### 1. Add new users in account for test runs
Add users into Harness account with random password and list them in [credentials.csv](./data/on-prem/credentials.csv)
These credentials will be used during test runs for performing authentication

> eg: auto_perf_1597@mailinator.com:Test@123

#### Multiple users can be added to Harness by following the below steps.

Step1: Run mongo query to add admin user into harness User group user. Replace the username with valid email who is part of account admin in the account. This user should be used to provision the users in step2

       db.harnessUserGroups.insertOne({'name':'readOnly','memberIds':db.users.distinct('_id',{email:"<username>"})})

Step2: Execute script [user_provision.sh](./data/scripts/user_provision.sh) (update the inputs and run)

       	url=http://<ip> : ip address or complete URL of Harness .
       	username=<username> # user email should be same as user used in Step1.
       	password=<password> # Password of the user.
            userCount=1   # No of users needs to be provisioned.
       	new_email_id_prefix="harness_perftest_"  # Prefix for new users.
       	new_email_id_domain="@test.com"	 # email domain for the new user.
       	new_user_password="random_password" # any random password. we are keeping the same password for all the users.

#### 2. Add github userIds and tokens as Harness secrets (via below script)
#### 3. Add github repo url, branch name as Harness variable (via below script)
Required to perform git clone and push Harness pipeline yaml

#### 4. Add kubernetes cluster namespace as Harness variable (via below script)
Namespace in which build pods are created while running pipelines

#### 5. Populate Harness data (via below script)
Add 100 organisations and 20 projects in each organisation to populate some data in Harness account

Above 2, 3, 4 can be added using script [testdata.sh](./data/scripts/testdata.sh)  
**Imp:** Change inputs in script to valid values and EXECUTE

#### 6. Add delegate in Harness account with tag : perf-delegate

#### 7. Test execution via webhook triggers
For test class - [CI_PIPELINE_WEBHOOK_RUN](./locust_tasks/ci_pipeline_webhook_run.py) update webhook payload on [ci_webhook_payload.json](./resources/NG/pipeline/ci/ci_webhook_payload.json)  
For test class - [CD_PIPELINE_WEBHOOK_RUN](./locust_tasks/cd_pipeline_webhook_run.py) update webhook payload on [cd_webhook_payload.json](./resources/NG/pipeline/cd/cd_webhook_payload.json)  
**Note:** Make sure to include {"zen": "$zen"} inside webhook payload


### [Locust installation](#)

#### Set up Locust on local machine
1. Install python3 ```brew install python3 ```  
2. Install Locust > ```pip3 install locust```
3. Append SMP certificates to python cacert.pem file  
   a. locate cacert.pem file via terminal `python -c "import certifi; print(certifi.where())"`   
4. Git clone
5. Update locust master ip to '0.0.0.0' in [variables.sh](./variables.sh)
6. Execute > ```locust -f locust_tasks/tasks```

#### Set up Locust on GCP cluster  
1. Git clone
2. Connect to GCP cluster
3. Procure static IP address
4. Add SMP certificates to [smp_certificates.pem](./smp_certifcates.pem)
5. Update GCP project, cluster namespace and locust master ip (static ip) in [variables.sh](./variables.sh)
5. Execute [install.sh](./install.sh) under cloned directory `./install.sh`

### [Test Execution](#)

#### Execute test scripts via locust webUI

1. Navigate to http://0.0.0.0:8089/ (on local setup) or http://Locust_MASTER_IP:8089     

  
2. Parameters
``` 
Number of users : Total concurrent users [eg: 1]

Spawn rate : Time to spawn all users [eg: 1 (in seconds)]

Host : <Harness URL> [eg: http://<ip_address>]

Run time : Test duration [eg: 5m]
note: Click on Advanced options to view this field

Test scenario : Test class to execute 
eg: CI_CREATE_PIPELINE,CI_EXECUTE_PIPELINE (single or comma separated class names)

Pipeline url (optional) : Pipeline url to execute ‘n’ times 
eg: http://<ip_address>/ng/account/DbSRs-u5QgukRP_ODtvGkw/ci/orgs/default/projects/ScaleTestPOC/pipelines/CITest/pipeline-studio/?storeType=INLINE
Pick pipeline link from Harness UI Left menu > Builds > Select Project > Click Pipelines on left > Click on pipeline name

Pipeline execution count (optional) : no. of times pipeline should run [eg: 50]

```
![](./docs/img/locust_params.png)

#### Testdata setup 

There might be a slight delay of approximately 60 seconds before the test execution begins, as pre-requisite data is being generated  
STATUS = TESTDATA SETUP is set on locust web UI during this phase  
**Note:** Any error during this phase is not visible on locust WebUI and had to be checked in locust master logs

![](./docs/img/testdata_setup.png)

#### Execute test scripts via Curl

> curl --location '<LOCUST_MASTER_IP>:8089/swarm' \
--header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
--data 'user_count=2&spawn_rate=1&host=<HARNESS_SMP_URL>&run_time=2m&test_scenario=CI_CREATE_PIPELINE,CI_EXECUTE_PIPELINE&pipeline_url=&pipeline_execution_count=1'  
  

### [View Results](#)

#### Statistics 
> capture no. of requests, failures, 99%ile, avg response time, etc.  

Navigate to locust server URL while tests are running to view real time metrics

![](./docs/img/statistics.png)


#### Locust Reports
> capture requests, failures, etc.

![](./docs/img/reports.png)


### [Test Scripts (scenarios)](#)

  
  

| Scenario                               | Pre-requisite data                                                                                                                                                                                                                                                                                                                                                                                                             | Locust params                                                                                                                                         | Comments                                                                                                                                                       |
|:---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Execute CI pipeline 'n' times          | Create Organization, project, connectors, <br/>step template and pipeline                                                                                                                                                                                                                                                                                                                                                      | Test scenario : CI_PIPELINE_RUN<br/> Pipeline url: blank<br/>Pipeline execution count : 10                                                            |                                                                                                                                                                |
| Execute CI pipeline 'n' times (gitX)   | Create Organization, project, 15 github code repo connectors, 15 gitX <br/>(step template, stage template, pipelines, pipeline input set, pipeline triggers) <br/> <br/>Manual steps :<br/> 1. Add Harness pipeline trigger <br/>2. Get webhook payload under github repo <br/>3. Add one property {"zen": "$zen"} in webhook payload <br/>4. Replace webhook payload in resources/NG/pipeline/ci/ci_webhook_payload.json file | Test scenario : CI_PIPELINE_REMOTE_RUN<br/> Pipeline url: blank<br/>Pipeline execution count : 10                                                     | Pipeline is triggered via webhook and each pipeline_execution_count triggers 15 pipelines <br/> <br/>To execute 1500 pipelines - set pipeline_execution_count = 100 |
| SAVE - GET - UPDATE CI pipeline        | Create Organization, project, 15 github connectors, pipeline template                                                                                                                                                                                                                                                                                                                                                          | Test scenario : CI_PIPELINE_SAVE<br/> Pipeline url: blank<br/>Pipeline execution count : 0                                                            |                                                            ‘n’ users will Save - Get - Update CI pipeline concurrently and repeat until duration                                                                                                    | 
| SAVE - GET - UPDATE CI pipeline (gitX) | Create Organization, project, 15 github connectors, 15 gitX step template, <br/>15 gitX stage templates                                                                                                                                                                                                                                                                                                                        | Test scenario : CI_PIPELINE_REMOTE_SAVE<br/> Pipeline url: blank<br/>Pipeline execution count : 0                                                     |                                                 ‘n’ users will Save - Get - Update gitX CI pipeline concurrently and repeat until duration                                                                                                               |
| Trigger pipeline or webhook 'n' times  | Find pipeline link - Open Harness left nav -> Builds -> Select project -> <br/>Click on pipelines -> Click on pipeline name -> copy pipeline url<br/><br/> eg: http://<ip_address>/ng/account/DbSRs-u5QgukRP_ODtvGkw/ci/orgs/default<br/>/projects/ScaleTestPOC/pipelines/CITest/pipeline-studio/?storeType=INLINE                                                                                                             | Test scenario : TRIGGER_PIPELINE<br/> Pipeline url: <URL><br/>Pipeline execution count : 10                                                           |                                                                                                                                                                |
| User behaviour under steady load       | Create Organizations, projects, connectors, 200 pipeline and execute them                                                                                                                                                                                                                                                                                                                                                      | Test scenario : CI_CREATE_PIPELINE,CI_EXECUTE_PIPELINE,<br/>CI_UPDATE_PIPELINE,CI_VIEW_EXECUTION<br/> Pipeline url: blank<br/>Pipeline execution count : 0 |                                                                                                                                                                |
| Execute CD pipeline 'n' times          | Create Organization, project, K8s service, env, infra, connectors, pipeline                                                                                                                                                                                                                                                                                                                                                    | Test scenario : CD_PIPELINE_RUN<br/> Pipeline url: blank<br/>Pipeline execution count : n                                                            |                                                                                                                                                                |
 
