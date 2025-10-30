#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPO_BASE="housing-crisis"
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "=========================================="
echo "Pushing Images to ECR"
echo "=========================================="
echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

echo -e "\n[1/4] Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo -e "\n[2/4] Creating ECR repositories (if not exist)..."
for repo in base ml jupyter; do
    aws ecr describe-repositories \
        --repository-names ${ECR_REPO_BASE}-${repo} \
        --region ${AWS_REGION} 2>/dev/null || \
    aws ecr create-repository \
        --repository-name ${ECR_REPO_BASE}-${repo} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo "  ✓ ${ECR_REPO_BASE}-${repo}"
done

echo -e "\n[3/4] Pushing images to ECR..."
for repo in base ml jupyter; do
    echo "  Pushing ${ECR_REPO_BASE}-${repo}:${IMAGE_TAG}..."
    docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-${repo}:${IMAGE_TAG}
done

echo -e "\n[4/4] Tagging images as 'latest'..."
for repo in base ml jupyter; do
    MANIFEST=$(aws ecr batch-get-image \
        --repository-name ${ECR_REPO_BASE}-${repo} \
        --image-ids imageTag=${IMAGE_TAG} \
        --query 'images[].imageManifest' \
        --output text \
        --region ${AWS_REGION})

    aws ecr put-image \
        --repository-name ${ECR_REPO_BASE}-${repo} \
        --image-tag latest \
        --image-manifest "$MANIFEST" \
        --region ${AWS_REGION} 2>/dev/null || true
    echo "  ✓ ${ECR_REPO_BASE}-${repo}:latest"
done

echo -e "\n=========================================="
echo "Push Complete!"
echo "=========================================="
echo "ECR Images:"
echo "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-ml:${IMAGE_TAG}"
echo "  - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-jupyter:${IMAGE_TAG}"
echo ""
echo "Next: Run ./scripts/deploy.sh to deploy to EKS"
echo "=========================================="
