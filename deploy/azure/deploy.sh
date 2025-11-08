#!/bin/bash

set -e

echo "======================================================================"
echo "CloudEasyML - Azure AKS Deployment"
echo "======================================================================"

if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    export AZURE_RESOURCE_GROUP="cloudeasyml-rg"
fi

if [ -z "$AZURE_LOCATION" ]; then
    export AZURE_LOCATION="eastus"
fi

export CLUSTER_NAME="cloudeasyml-cluster"
export ACR_NAME="cloudeasymlacr${RANDOM}"

echo "Resource Group: $AZURE_RESOURCE_GROUP"
echo "Location: $AZURE_LOCATION"
echo "Cluster Name: $CLUSTER_NAME"
echo "ACR Name: $ACR_NAME"
echo ""

echo "Creating resource group..."
az group create \
    --name $AZURE_RESOURCE_GROUP \
    --location $AZURE_LOCATION

echo "Creating Container Registry..."
az acr create \
    --resource-group $AZURE_RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Standard

read -p "Create AKS cluster? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating AKS cluster with GPU support..."
    az aks create \
        --resource-group $AZURE_RESOURCE_GROUP \
        --name $CLUSTER_NAME \
        --node-count 2 \
        --node-vm-size Standard_NC6s_v3 \
        --enable-cluster-autoscaler \
        --min-count 1 \
        --max-count 4 \
        --attach-acr $ACR_NAME \
        --generate-ssh-keys
fi

echo "Installing NVIDIA GPU plugin..."
az aks install-cli
az aks get-credentials \
    --resource-group $AZURE_RESOURCE_GROUP \
    --name $CLUSTER_NAME

kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

echo "Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image cloudeasyml:latest \
    --file deploy/azure/Dockerfile \
    .

echo "Deploying to Kubernetes..."
kubectl apply -f deploy/azure/k8s/

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
