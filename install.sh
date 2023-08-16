#!/bin/sh
source ./variables.sh
# delete existing locust deployments
./delete.sh

# create namespace = $NAMESPACE (if not exists)
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "Namespace $NAMESPACE already exists."
else
  kubectl create namespace "$NAMESPACE"
  echo "Namespace $NAMESPACE was successfully created."
fi

# set GCP project
gcloud config set project $PROJECT

# set locust mater url
file="./locust_tasks/utilities/utils.py"
perl -pi -e "s/<LOCUST_MASTER_URL>/$LOCUST_MASTER_URL/g" ${file}

# build locust image
if $build_locust_image; then
  gcloud builds submit --tag gcr.io/$PROJECT/locust_tasks:latest .
fi

# deploy locust
./deploy.sh
