#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-ml-cluster}
IMAGE_TAG=${IMAGE_TAG:-latest}
JOB_ID=$(date +%Y%m%d-%H%M%S)
FRED_API_KEY=${FRED_API_KEY:-""}

echo "=========================================="
echo "Starting Training Job on EKS"
echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

if [ -z "$FRED_API_KEY" ]; then
    echo "WARNING: FRED_API_KEY not set. Training may fail."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "\n[1/2] Updating kubeconfig..."
aws eks update-kubeconfig \
    --name ${EKS_CLUSTER_NAME} \
    --region ${AWS_REGION}

echo -e "\n[2/2] Submitting training job..."
export AWS_ACCOUNT_ID AWS_REGION IMAGE_TAG JOB_ID FRED_API_KEY
envsubst < k8s/job.yaml | kubectl apply -f -

echo -e "\n=========================================="
echo "Training Job Submitted!"
echo "=========================================="
echo "Job Name: housing-crisis-training-${JOB_ID}"
echo ""
echo "Monitor job:"
echo "  kubectl get jobs -n ml-jobs -w"
echo ""
echo "View logs:"
echo "  kubectl logs -f job/housing-crisis-training-${JOB_ID} -n ml-jobs"
echo ""
echo "Check completion:"
echo "  kubectl get job housing-crisis-training-${JOB_ID} -n ml-jobs"
echo "=========================================="
