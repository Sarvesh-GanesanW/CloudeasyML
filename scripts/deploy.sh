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

echo -e "\n[1/6] Updating kubeconfig..."
aws eks update-kubeconfig \
    --name ${EKS_CLUSTER_NAME} \
    --region ${AWS_REGION}

echo -e "\n[2/6] Creating namespaces..."
kubectl create namespace ml-inference --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ml-jobs --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ml-dev --dry-run=client -o yaml | kubectl apply -f -

echo -e "\n[3/6] Applying PVCs..."
export AWS_ACCOUNT_ID AWS_REGION
envsubst < k8s/pvc.yaml | kubectl apply -f -

echo -e "\n[4/6] Deploying inference service..."
export AWS_ACCOUNT_ID AWS_REGION IMAGE_TAG
envsubst < k8s/deployment.yaml | kubectl apply -f -

echo -e "\n[5/6] Deploying Jupyter (optional)..."
read -p "Deploy Jupyter notebook server? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    envsubst < k8s/jupyter-deployment.yaml | kubectl apply -f -
fi

echo -e "\n[6/6] Checking deployment status..."
kubectl rollout status deployment/housing-crisis-inference -n ml-inference --timeout=300s

echo -e "\n=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Check pods:"
echo "  kubectl get pods -n ml-inference"
echo ""
echo "Check service:"
echo "  kubectl get svc -n ml-inference"
echo ""
echo "View logs:"
echo "  kubectl logs -f deployment/housing-crisis-inference -n ml-inference"
echo ""
echo "Port forward for testing:"
echo "  kubectl port-forward svc/housing-crisis-inference 8000:80 -n ml-inference"
echo ""
echo "Test API:"
echo "  curl http://localhost:8000/health"
echo "=========================================="
