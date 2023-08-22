# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Start with a base locust:1.5.1 image
FROM locustio/locust:2.5.0

# Add the external tasks directory into /tasks
ADD locust_tasks /locust_tasks

#Add Cluster credentials
ADD data /data

#Add resources
ADD resources /resources

#Add smp certificates file
ADD smp_certifcates.pem /smp_certifcates.pem

ADD run.sh /run.sh

# Install the required dependencies via pip
# RUN pip3 install -r /locust_tasks/requirements.txt

# Expose the required Locust ports
EXPOSE 5557 5558 8089

#Changing the permissions and Set script to be executable
USER root
RUN pip3 install --upgrade pip
RUN pip3 install -r /locust_tasks/requirements.txt

RUN chmod 777 -R /resources/*

ENV PYTHONPATH "${PYTHONPATH}:/"
ENV LOCUST_MASTER_IP=to_be_replaced_from_variables.sh

# Start Locust using LOCUS_OPTS environment variable
ENTRYPOINT ["/run.sh"]