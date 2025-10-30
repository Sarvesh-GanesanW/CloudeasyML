#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPO_BASE="housing-crisis"
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "=========================================="
echo "Building Housing Crisis ML Docker Images"
echo "=========================================="
echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

cd "$(dirname "$0")/.."

echo -e "\n[1/4] Building base image..."
docker build \
    -f docker/Dockerfile.base \
    -t ${ECR_REPO_BASE}-base:${IMAGE_TAG} \
    .

echo -e "\n[2/4] Building ML image..."
docker build \
    -f docker/Dockerfile \
    --build-arg BASE_IMAGE=${ECR_REPO_BASE}-base:${IMAGE_TAG} \
    -t ${ECR_REPO_BASE}-ml:${IMAGE_TAG} \
    .

echo -e "\n[3/4] Building Jupyter image..."
docker build \
    -f docker/Dockerfile.jupyter \
    --build-arg BASE_IMAGE=${ECR_REPO_BASE}-ml:${IMAGE_TAG} \
    -t ${ECR_REPO_BASE}-jupyter:${IMAGE_TAG} \
    .

echo -e "\n[4/4] Tagging images for ECR..."
docker tag ${ECR_REPO_BASE}-base:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-base:${IMAGE_TAG}

docker tag ${ECR_REPO_BASE}-ml:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-ml:${IMAGE_TAG}

docker tag ${ECR_REPO_BASE}-jupyter:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_BASE}-jupyter:${IMAGE_TAG}

echo -e "\n=========================================="
echo "Build Complete!"
echo "=========================================="
echo "Images:"
echo "  - ${ECR_REPO_BASE}-base:${IMAGE_TAG}"
echo "  - ${ECR_REPO_BASE}-ml:${IMAGE_TAG}"
echo "  - ${ECR_REPO_BASE}-jupyter:${IMAGE_TAG}"
echo ""
echo "Next: Run ./scripts/push.sh to push to ECR"
echo "=========================================="
