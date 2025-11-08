#!/bin/bash

set -e

echo "======================================================================"
echo "CloudEasyML - AWS EKS Deployment"
echo "======================================================================"

if [ -z "$AWS_REGION" ]; then
    export AWS_REGION="us-east-1"
fi

if [ -z "$AWS_ACCOUNT_ID" ]; then
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

export CLUSTER_NAME="cloudeasyml-cluster"
export ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/cloudeasyml"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Cluster Name: $CLUSTER_NAME"
echo ""

read -p "Create EKS cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating EKS cluster..."
    eksctl create cluster \
        --name $CLUSTER_NAME \
        --region $AWS_REGION \
        --nodegroup-name gpu-nodes \
        --node-type g5.xlarge \
        --nodes 2 \
        --nodes-min 1 \
        --nodes-max 4 \
        --managed \
        --install-nvidia-plugin
fi

echo "Creating ECR repository..."
aws ecr create-repository \
    --repository-name cloudeasyml \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    || echo "Repository already exists"

echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO

echo "Building Docker image..."
docker build -t cloudeasyml:latest -f deploy/aws/Dockerfile .

echo "Tagging image..."
docker tag cloudeasyml:latest $ECR_REPO:latest

echo "Pushing to ECR..."
docker push $ECR_REPO:latest

echo "Updating kubeconfig..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION

echo "Deploying to Kubernetes..."
kubectl apply -f deploy/aws/k8s/

echo "Waiting for LoadBalancer..."
kubectl wait --for=condition=available --timeout=300s deployment/cloudeasyml -n ml-platform

echo ""
echo "======================================================================"
echo "Deployment Complete!"
echo "======================================================================"
echo ""

ALB_URL=$(kubectl get ingress -n ml-platform cloudeasyml-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending...")

echo "API URL: http://${ALB_URL}"
echo "Health: http://${ALB_URL}/health"
echo "Admin: http://${ALB_URL}/admin"
echo ""
echo "Use 'kubectl logs -f deployment/cloudeasyml -n ml-platform' to view logs"
echo "======================================================================"
