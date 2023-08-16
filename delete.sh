#!/bin/bash
source ./variables.sh
kubectl delete deployment locust-worker -n $NAMESPACE
kubectl delete deployment locust-master -n $NAMESPACE
