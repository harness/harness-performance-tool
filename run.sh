#!/bin/bash

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


LOCUST="env host=$TARGET_HOST cluster=$CLUSTER /usr/local/bin/locust"
#LOCUS_OPTS="-f /locust_tasks/tasks.py --headless --csv=booperf -u 1 -r 1 --run-time 60s --stop-timeout 99 --expect-workers 1 --host=$TARGET_HOST"
LOCUS_OPTS="-f /locust_tasks/tasks.py --host=$TARGET_HOST"
#LOCUS_OPTS="-f /locust_tasks/tasks.py -u 5 -t 60 --headless -i 10 --csv=booperf --host=$TARGET_HOST"
LOCUST_OPTS_WORKER="-f /locust_tasks/tasks.py --host=$TARGET_HOST"
LOCUST_MODE=${LOCUST_MODE:-standalone}

if [[ "$LOCUST_MODE" = "master" ]]; then
    LOCUS_OPTS="$LOCUS_OPTS --master"
elif [[ "$LOCUST_MODE" = "worker" ]]; then
    LOCUS_OPTS="$LOCUST_OPTS_WORKER --worker --master-host=$LOCUST_MASTER"
fi

echo "$LOCUST $LOCUS_OPTS"

$LOCUST $LOCUS_OPTS
