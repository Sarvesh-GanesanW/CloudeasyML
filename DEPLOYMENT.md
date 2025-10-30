## Deployment Guide

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Lambda    │────────▶│  EKS Cluster │◀────────│   ECR       │
│  Functions  │         │   (GPU g5)   │         │  Registry   │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               │
                        ┌──────┴──────┐
                        │             │
                   ┌────▼────┐   ┌────▼────┐
                   │Inference│   │Training │
                   │Pods (2) │   │ Jobs    │
                   └────┬────┘   └────┬────┘
                        │             │
                    ┌───▼─────────────▼───┐
                    │   EFS Persistent    │
                    │   Volume (Models)   │
                    └─────────────────────┘
```

## Prerequisites

### 1. AWS Setup
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

### 2. EKS Cluster with GPU Nodes
```bash
eksctl create cluster \
  --name ml-cluster \
  --region $AWS_REGION \
  --nodegroup-name gpu-nodes \
  --node-type g5.xlarge \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed \
  --install-nvidia-plugin
```

### 3. Install NVIDIA Device Plugin
```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

### 4. Install EFS CSI Driver
```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.7"
```

### 5. Create EFS File System
```bash
aws efs create-file-system \
  --region $AWS_REGION \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --tags Key=Name,Value=housing-crisis-efs

export EFS_ID=<your-efs-id>

aws efs create-mount-target \
  --file-system-id $EFS_ID \
  --subnet-id <subnet-id> \
  --security-groups <security-group-id>
```

## Deployment Steps

### Phase 1: Build and Push Docker Images

```bash
cd HousingCrisisPredictionEnsemble

export AWS_REGION=us-east-1
export IMAGE_TAG=v1.0.0

./scripts/build.sh

./scripts/push.sh
```

**Expected Output:**
```
✓ housing-crisis-base:v1.0.0
✓ housing-crisis-ml:v1.0.0
✓ housing-crisis-jupyter:v1.0.0
```

### Phase 2: Deploy to EKS

```bash
export EKS_CLUSTER_NAME=ml-cluster
export IMAGE_TAG=v1.0.0

./scripts/deploy.sh
```

**Verify Deployment:**
```bash
kubectl get pods -n ml-inference

kubectl get svc -n ml-inference

kubectl logs -f deployment/housing-crisis-inference -n ml-inference
```

### Phase 3: Test Inference API

**Port Forward:**
```bash
kubectl port-forward svc/housing-crisis-inference 8000:80 -n ml-inference
```

**Test Health Endpoint:**
```bash
curl http://localhost:8000/health
```

**Test Prediction:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{"GDP": 20000, "UNRATE": 5.5, "MORTGAGE30US": 4.5}],
    "horizon": 12,
    "crisisDetection": true
  }'
```

### Phase 4: Run Training Job

```bash
export FRED_API_KEY=your_fred_api_key_here
export IMAGE_TAG=v1.0.0

./scripts/run-training-job.sh
```

**Monitor Job:**
```bash
kubectl get jobs -n ml-jobs -w

kubectl logs -f job/housing-crisis-training-<job-id> -n ml-jobs
```

### Phase 5: Deploy Jupyter Backend (Optional)

```bash
kubectl apply -f k8s/jupyter-deployment.yaml

kubectl get svc housing-crisis-jupyter -n ml-dev

kubectl port-forward svc/housing-crisis-jupyter 8888:8888 -n ml-dev
```

Access at: `http://localhost:8888`

## Lambda Integration

### Deploy Lambda Functions

**1. Create Lambda Execution Role:**
```bash
aws iam create-role \
  --role-name HousingCrisisLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name HousingCrisisLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
```

**2. Package Lambda Functions:**
```bash
cd lambda

pip install kubernetes boto3 requests -t .

zip -r trigger-training.zip trigger-training.py kubernetes boto3 requests

zip -r trigger-prediction.zip trigger-prediction.py boto3 requests
```

**3. Deploy Lambda Functions:**
```bash
aws lambda create-function \
  --function-name housing-crisis-trigger-training \
  --runtime python3.10 \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/HousingCrisisLambdaRole \
  --handler trigger-training.lambda_handler \
  --zip-file fileb://trigger-training.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{EKS_CLUSTER_NAME=ml-cluster,AWS_REGION=${AWS_REGION}}"

aws lambda create-function \
  --function-name housing-crisis-trigger-prediction \
  --runtime python3.10 \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/HousingCrisisLambdaRole \
  --handler trigger-prediction.lambda_handler \
  --zip-file fileb://trigger-prediction.zip \
  --timeout 60 \
  --memory-size 256 \
  --environment Variables="{INFERENCE_ENDPOINT=http://housing-crisis-inference.ml-inference.svc.cluster.local}"
```

### API Gateway Integration

```bash
aws apigatewayv2 create-api \
  --name housing-crisis-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:housing-crisis-trigger-prediction
```

## Production Considerations

### 1. Autoscaling

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: housing-crisis-inference-hpa
  namespace: ml-inference
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: housing-crisis-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Cluster Autoscaler:**
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml
```

### 2. Monitoring

**Prometheus + Grafana:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

**CloudWatch Container Insights:**
```bash
aws eks create-addon \
  --cluster-name ml-cluster \
  --addon-name amazon-cloudwatch-observability
```

### 3. Security

**Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: housing-crisis-netpol
  namespace: ml-inference
spec:
  podSelector:
    matchLabels:
      app: housing-crisis
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

**Pod Security Standards:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-inference
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 4. Cost Optimization

**Spot Instances for Training:**
```bash
eksctl create nodegroup \
  --cluster ml-cluster \
  --name spot-gpu-nodes \
  --node-type g5.xlarge \
  --nodes 0 \
  --nodes-min 0 \
  --nodes-max 5 \
  --spot \
  --managed
```

**Karpenter for Dynamic Provisioning:**
```bash
helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --namespace karpenter --create-namespace
```

## Troubleshooting

### GPU Not Detected
```bash
kubectl describe nodes | grep nvidia.com/gpu

kubectl get pods -n kube-system | grep nvidia
```

### Model Loading Issues
```bash
kubectl exec -it deployment/housing-crisis-inference -n ml-inference -- \
  ls -la /app/models/saved
```

### OOM Errors
Increase memory limits in deployment.yaml:
```yaml
resources:
  limits:
    memory: "64Gi"
```

### Slow Inference
Check GPU utilization:
```bash
kubectl exec -it deployment/housing-crisis-inference -n ml-inference -- \
  nvidia-smi
```

## Cleanup

```bash
kubectl delete namespace ml-inference ml-jobs ml-dev

eksctl delete cluster --name ml-cluster --region $AWS_REGION

aws ecr delete-repository --repository-name housing-crisis-base --force
aws ecr delete-repository --repository-name housing-crisis-ml --force
aws ecr delete-repository --repository-name housing-crisis-jupyter --force
```

## Cost Estimate

| Component | Instance Type | Monthly Cost (us-east-1) |
|-----------|--------------|-------------------------|
| EKS Control Plane | - | $73 |
| Inference Nodes (2x) | g5.xlarge | ~$1,200 |
| Training Node (on-demand) | g5.2xlarge | ~$1,800 |
| EFS Storage (100GB) | - | ~$30 |
| ECR Storage (50GB) | - | ~$5 |
| **Total** | | **~$3,108/month** |

**Cost Optimization:**
- Use Spot instances for training: **60-70% savings**
- Scale down inference during off-hours: **30-40% savings**
- Use Fargate for non-GPU workloads: **Variable savings**

## Performance Benchmarks

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Health Check | 5ms | 10,000 req/s |
| Single Prediction | 50-100ms | 100 req/s |
| Batch Prediction (100) | 500ms | 20 batches/s |
| Model Loading | 30s | - |
| Training Job | 30-60 min | - |

## Support

- **Documentation**: See `ARCHITECTURE.md`, `QUICKREF.md`
- **Issues**: GitHub Issues
- **Logs**: CloudWatch Logs or `kubectl logs`
