source ./variables.sh

rs_project="s/\$PROJECT/${PROJECT}/g"
rs_namespace="s/\$NAMESPACE/${NAMESPACE}/g"
rs_locust_master_url="s/\$LOCUST_MASTER_URL/${LOCUST_MASTER_URL}/g"

# apply the replacement
sed -e "${rs_project}" -e "${rs_namespace}" kubernetes-config/locust-master-controller.yaml > updated-locust-master-controller.yaml
kubectl apply -f updated-locust-master-controller.yaml
rm updated-locust-master-controller.yaml

sed -e "${rs_locust_master_url}" -e "${rs_namespace}" kubernetes-config/locust-master-service.yaml > updated-locust-master-service.yaml
kubectl apply -f updated-locust-master-service.yaml
rm updated-locust-master-service.yaml

sed -e "${rs_project}" -e "${rs_namespace}" kubernetes-config/locust-worker-controller.yaml > updated-locust-worker-controller.yaml
kubectl apply -f updated-locust-worker-controller.yaml
rm updated-locust-worker-controller.yaml
