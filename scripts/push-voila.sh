#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "=========================================="
echo "Pushing Voilà Image to ECR"
echo "=========================================="

echo -e "\n[1/4] Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo -e "\n[2/4] Creating ECR repository..."
aws ecr describe-repositories \
    --repository-names housing-crisis-voila \
    --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository \
    --repository-name housing-crisis-voila \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true

echo -e "\n[3/4] Pushing image..."
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-voila:${IMAGE_TAG}

echo -e "\n[4/4] Tagging as latest..."
MANIFEST=$(aws ecr batch-get-image \
    --repository-name housing-crisis-voila \
    --image-ids imageTag=${IMAGE_TAG} \
    --query 'images[].imageManifest' \
    --output text \
    --region ${AWS_REGION})

aws ecr put-image \
    --repository-name housing-crisis-voila \
    --image-tag latest \
    --image-manifest "$MANIFEST" \
    --region ${AWS_REGION} 2>/dev/null || true

echo -e "\n=========================================="
echo "Push Complete!"
echo "=========================================="
echo "Image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-voila:${IMAGE_TAG}"
echo ""
echo "Deploy to EKS:"
echo "  kubectl apply -f k8s/voila-deployment.yaml"
echo "=========================================="
