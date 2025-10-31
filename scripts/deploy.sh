#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-ml-cluster}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "=========================================="
echo "Deploying to EKS"
echo "=========================================="
echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "EKS Cluster: $EKS_CLUSTER_NAME"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

echo -e "\n[1/7] Updating kubeconfig..."
aws eks update-kubeconfig \
    --name ${EKS_CLUSTER_NAME} \
    --region ${AWS_REGION}

echo -e "\n[2/7] Creating namespaces..."
kubectl create namespace ml-inference --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ml-jobs --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ml-dev --dry-run=client -o yaml | kubectl apply -f -

echo -e "\n[3/7] Applying PVCs..."
export AWS_ACCOUNT_ID AWS_REGION
envsubst < k8s/pvc.yaml | kubectl apply -f -

echo -e "\n[4/7] Deploying inference service..."
export AWS_ACCOUNT_ID AWS_REGION IMAGE_TAG
envsubst < k8s/deployment.yaml | kubectl apply -f -

echo -e "\n[5/7] Deploying JupyterLab backend..."
envsubst < k8s/jupyter-deployment.yaml | kubectl apply -f -

echo -e "\n[6/7] Deploying ALB Ingress..."
envsubst < k8s/ingress.yaml | kubectl apply -f -

echo -e "\n[7/7] Checking deployment status..."
kubectl rollout status deployment/housing-crisis-inference -n ml-inference --timeout=300s
kubectl rollout status deployment/housing-crisis-jupyter -n ml-inference --timeout=300s

echo -e "\n=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Waiting for ALB to be provisioned..."
sleep 10

ALB_URL=$(kubectl get ingress housing-crisis-ingress -n ml-inference -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")

echo ""
echo "Application URLs:"
echo "  JupyterLab: http://${ALB_URL}/"
echo "  API: http://${ALB_URL}/api/health"
echo ""
echo "Get Jupyter token:"
echo "  kubectl logs -n ml-inference deployment/housing-crisis-jupyter | grep 'token='"
echo ""
echo "Check pods:"
echo "  kubectl get pods -n ml-inference"
echo ""
echo "Check ingress:"
echo "  kubectl get ingress -n ml-inference"
echo ""
echo "View API logs:"
echo "  kubectl logs -f deployment/housing-crisis-inference -n ml-inference"
echo ""
echo "View Jupyter logs:"
echo "  kubectl logs -f deployment/housing-crisis-jupyter -n ml-inference"
echo ""
echo "Port forward for local testing:"
echo "  kubectl port-forward svc/housing-crisis-inference 8000:80 -n ml-inference"
echo "  kubectl port-forward svc/housing-crisis-jupyter 8888:8888 -n ml-inference"
echo ""
echo "Note: ALB provisioning takes 2-3 minutes. If URL shows 'pending', wait and run:"
echo "  kubectl get ingress -n ml-inference"
echo "=========================================="
