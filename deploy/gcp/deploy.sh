#!/bin/bash

set -e

echo "======================================================================"
echo "CloudEasyML - GCP GKE Deployment"
echo "======================================================================"

if [ -z "$GCP_PROJECT" ]; then
    echo "Error: GCP_PROJECT not set"
    exit 1
fi

if [ -z "$GCP_REGION" ]; then
    export GCP_REGION="us-central1"
fi

export CLUSTER_NAME="cloudeasyml-cluster"
export GCR_REPO="gcr.io/${GCP_PROJECT}/cloudeasyml"

echo "GCP Project: $GCP_PROJECT"
echo "GCP Region: $GCP_REGION"
echo "Cluster Name: $CLUSTER_NAME"
echo ""

read -p "Create GKE cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating GKE cluster with GPU support..."
    gcloud container clusters create $CLUSTER_NAME \
        --region $GCP_REGION \
        --machine-type n1-standard-4 \
        --accelerator type=nvidia-tesla-t4,count=1 \
        --num-nodes 2 \
        --min-nodes 1 \
        --max-nodes 4 \
        --enable-autoscaling \
        --enable-autorepair \
        --enable-autoupgrade \
        --addons HorizontalPodAutoscaling,HttpLoadBalancing
fi

echo "Installing NVIDIA GPU drivers..."
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

echo "Building Docker image..."
docker build -t cloudeasyml:latest -f deploy/gcp/Dockerfile .

echo "Tagging for GCR..."
docker tag cloudeasyml:latest $GCR_REPO:latest

echo "Pushing to GCR..."
docker push $GCR_REPO:latest

echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --region $GCP_REGION

echo "Deploying to Kubernetes..."
kubectl apply -f deploy/gcp/k8s/

echo "Waiting for deployment..."
kubectl wait --for=condition=available --timeout=300s deployment/cloudeasyml -n ml-platform

echo ""
echo "======================================================================"
echo "Deployment Complete!"
echo "======================================================================"
echo ""

EXTERNAL_IP=$(kubectl get service cloudeasyml -n ml-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending...")

echo "API URL: http://${EXTERNAL_IP}:8000"
echo "Health: http://${EXTERNAL_IP}:8000/health"
echo "Admin: http://${EXTERNAL_IP}:8000/admin"
echo ""
echo "======================================================================"
