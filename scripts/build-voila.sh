#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "=========================================="
echo "Building Voilà Dashboard Image"
echo "=========================================="
echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

cd "$(dirname "$0")/.."

echo -e "\n[1/3] Ensuring ML base image exists..."
if ! docker image inspect housing-crisis-ml:${IMAGE_TAG} &>/dev/null; then
    echo "ML base image not found. Building..."
    ./scripts/build.sh
fi

echo -e "\n[2/3] Building Voilà image..."
docker build \
    -f docker/Dockerfile.voila \
    --build-arg BASE_IMAGE=housing-crisis-ml:${IMAGE_TAG} \
    -t housing-crisis-voila:${IMAGE_TAG} \
    .

echo -e "\n[3/3] Tagging for ECR..."
docker tag housing-crisis-voila:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-voila:${IMAGE_TAG}

echo -e "\n=========================================="
echo "Build Complete!"
echo "=========================================="
echo "Image: housing-crisis-voila:${IMAGE_TAG}"
echo ""
echo "Test locally:"
echo "  docker run -p 8866:8866 housing-crisis-voila:${IMAGE_TAG}"
echo "  Open http://localhost:8866"
echo ""
echo "Push to ECR:"
echo "  ./scripts/push-voila.sh"
echo "=========================================="
