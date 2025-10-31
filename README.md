# Housing Crisis Prediction Ensemble

Multi-modal ML system for real-time housing market crisis prediction and policy recommendation.

## Features

- **Multi-Model Ensemble**: XGBoost, CatBoost, TimesFM, Chronos, STGNN, AutoGluon
- **GPU Auto-Detection**: Works on CPU or GPU without configuration changes
- **Crisis Detection**: Real-time risk scoring and policy recommendations
- **Interactive Jupyter Interface**: Full data science workflow with code visibility
- **FastAPI Backend**: RESTful API for predictions
- **Production Ready**: Docker + EKS + ALB deployment

## Quick Start (5 minutes)

```bash
# 1. Activate conda environment
conda activate hcpe

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run demo with synthetic data
./run_quickstart.sh
```

**What you get:**
- Synthetic 15-year housing/economic dataset
- 77 engineered features from 7 base indicators
- XGBoost + CatBoost ensemble trained
- Crisis detection analysis
- Policy recommendations

## Local Development

### Prerequisites
- Python 3.10+
- Conda (recommended)
- CUDA 11.8+ (optional, for GPU acceleration)

### Setup

```bash
# Create and activate environment
conda create -n hcpe python=3.12
conda activate hcpe

# Install core dependencies
pip install -r requirements.txt

# Optional: Install foundation models
pip install git+https://github.com/google-research/timesfm.git
pip install git+https://github.com/amazon-science/chronos-forecasting.git
```

### Run Jupyter Development Environment

```bash
# Terminal 1: Start API server
python src/api/server.py

# Terminal 2: Start JupyterLab
./run_jupyterlab.sh

# Open browser to: http://localhost:8888
# Open notebook: notebooks/housing_crisis_analysis.ipynb
```

**JupyterLab provides:**
- Full code editor with syntax highlighting
- Interactive notebook execution
- Terminal access
- File browser
- Data exploration and visualization
- Model training and evaluation

## Production Deployment (AWS EKS + ALB)

### Architecture

```
Internet
   ↓
Application Load Balancer (ALB)
   ↓
EKS Cluster (g5.xlarge GPU nodes)
   ├── JupyterLab Backend (Port 8888)
   ├── FastAPI Service (Port 8000)
   └── Training Jobs (Batch)
```

### Prerequisites

1. **AWS Account** with IAM permissions:
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonEKSClusterPolicy`
   - `AmazonEKSWorkerNodePolicy`
   - `ElasticLoadBalancingFullAccess`

2. **AWS CLI** configured:
```bash
aws configure
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-1
```

3. **kubectl** installed:
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

4. **eksctl** installed:
```bash
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

### Step 1: Create EKS Cluster with GPU

```bash
eksctl create cluster \
  --name housing-ml-cluster \
  --region us-east-1 \
  --nodegroup-name gpu-nodes \
  --node-type g5.xlarge \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed \
  --install-nvidia-plugin

# This takes ~15-20 minutes
```

### Step 2: Set Environment Variables

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export EKS_CLUSTER_NAME=housing-ml-cluster
export IMAGE_TAG=latest
```

### Step 3: Build and Push Docker Images

```bash
# Build images
./scripts/build.sh

# This builds:
# - housing-crisis-base: CUDA 12.1 + Conda + AWS CLI
# - housing-crisis-ml: ML models + dependencies
# - housing-crisis-jupyter: JupyterLab server

# Push to ECR
./scripts/push.sh

# Images pushed to:
# - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-base:latest
# - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-ml:latest
# - ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-jupyter:latest
```

### Step 4: Deploy to EKS

```bash
# Deploy JupyterLab + FastAPI + ALB
./scripts/deploy.sh

# This creates:
# - Namespace: ml-inference
# - JupyterLab deployment (port 8888)
# - FastAPI deployment (port 8000)
# - ALB Ingress
# - PersistentVolumeClaims for model storage
```

### Step 5: Access Services

```bash
# Get ALB URL
ALB_URL=$(kubectl get ingress -n ml-inference housing-crisis-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "JupyterLab: http://${ALB_URL}/jupyter"
echo "API: http://${ALB_URL}/api"
echo "Health: http://${ALB_URL}/api/health"

# Or use port-forward for testing
kubectl port-forward -n ml-inference svc/housing-crisis-jupyter 8888:8888
kubectl port-forward -n ml-inference svc/housing-crisis-api 8000:8000
```

### Step 6: JupyterLab Authentication

```bash
# Get Jupyter token
kubectl logs -n ml-inference deployment/housing-crisis-jupyter | grep "token="

# Look for line like:
# http://127.0.0.1:8888/?token=abc123def456...

# Access JupyterLab:
# http://${ALB_URL}/jupyter?token=abc123def456...
```

## Kubernetes Deployment Details

### JupyterLab Backend

```yaml
# k8s/jupyter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: housing-crisis-jupyter
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: jupyter
        image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/housing-crisis-jupyter:latest
        ports:
        - containerPort: 8888
        resources:
          requests:
            nvidia.com/gpu: "1"
            memory: "16Gi"
            cpu: "4"
          limits:
            nvidia.com/gpu: "1"
            memory: "32Gi"
            cpu: "8"
```

### Application Load Balancer

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: housing-crisis-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /jupyter
        pathType: Prefix
        backend:
          service:
            name: housing-crisis-jupyter
            port:
              number: 8888
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: housing-crisis-api
            port:
              number: 8000
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T12:00:00",
  "modelsLoaded": true
}
```

### Prediction Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "GDP": 25000,
      "CPIAUCSL": 300,
      "UNRATE": 5.5,
      "FEDFUNDS": 4.5,
      "MORTGAGE30US": 6.5,
      "HOUST": 1400
    }],
    "horizon": 12,
    "crisisDetection": true
  }'
```

Response:
```json
{
  "predictions": [221.5, 223.1, 224.7, ...],
  "horizon": 12,
  "crisisLevel": "LOW",
  "crisisScore": -0.257,
  "recommendations": [
    "Continue routine market monitoring",
    "Refine predictive models with latest data",
    "Conduct policy impact simulations"
  ]
}
```

## GPU Auto-Detection

The system automatically detects GPU availability:

```python
# Local with GPU
Training on: NVIDIA GeForce RTX 3060
XGBoost: gpu_hist
CatBoost: GPU

# Docker without GPU
Training on: CPU
XGBoost: hist
CatBoost: CPU

# EKS with g5.xlarge
Training on: NVIDIA A10G
XGBoost: gpu_hist
CatBoost: GPU
```

No configuration changes needed - same code works everywhere.

## Cost Breakdown

### Local Development: $0
- Uses your local machine
- No cloud charges

### AWS Production (EKS + ALB)

**Minimum Setup:**
- EKS Control Plane: $73/month
- 2x g5.xlarge nodes: $1,460/month
- ALB: $23/month
- EFS Storage: $30/month
- **Total: ~$1,586/month**

**With Spot Instances (60% savings):**
- 2x g5.xlarge spot: $584/month
- **Total: ~$710/month**

**Recommended for Testing:**
- 1x g5.xlarge on-demand: $730/month
- Use Spot for training jobs
- Scale down during off-hours
- **Total: ~$400-600/month**

## Monitoring and Operations

### View Logs

```bash
# JupyterLab logs
kubectl logs -f -n ml-inference deployment/housing-crisis-jupyter

# API logs
kubectl logs -f -n ml-inference deployment/housing-crisis-api

# All pods in namespace
kubectl logs -f -n ml-inference --all-containers=true
```

### Scale Deployment

```bash
# Scale JupyterLab (not recommended > 1)
kubectl scale deployment housing-crisis-jupyter --replicas=1 -n ml-inference

# Scale API
kubectl scale deployment housing-crisis-api --replicas=3 -n ml-inference
```

### Run Training Job

```bash
# Submit batch training job
./scripts/run-training-job.sh

# Monitor job
kubectl get jobs -n ml-jobs
kubectl logs -f -n ml-jobs job/housing-crisis-training-$(date +%Y%m%d)
```

### Delete Everything

```bash
# Delete all resources
kubectl delete namespace ml-inference ml-jobs

# Delete cluster
eksctl delete cluster --name housing-ml-cluster --region us-east-1
```

## Project Structure

```
HousingCrisisPredictionEnsemble/
├── config/
│   └── config.yaml                 # Model and pipeline configuration
├── data/
│   ├── raw/                        # Raw economic data
│   ├── processed/                  # Processed datasets
│   └── cache/                      # FRED API cache
├── docker/
│   ├── Dockerfile.base             # CUDA + Conda base image
│   ├── Dockerfile                  # ML models image
│   └── Dockerfile.jupyter          # JupyterLab image
├── k8s/
│   ├── jupyter-deployment.yaml     # JupyterLab deployment
│   ├── api-deployment.yaml         # FastAPI deployment
│   ├── ingress.yaml                # ALB ingress
│   ├── training-job.yaml           # Batch training job
│   └── pvc.yaml                    # Persistent storage
├── notebooks/
│   └── housing_crisis_analysis.ipynb  # Full analysis notebook
├── scripts/
│   ├── build.sh                    # Build Docker images
│   ├── push.sh                     # Push to ECR
│   └── deploy.sh                   # Deploy to EKS
├── src/
│   ├── api/
│   │   └── server.py               # FastAPI backend
│   ├── data/
│   │   ├── dataCollector.py        # FRED + Zillow data
│   │   └── featureEngineer.py      # Feature engineering
│   ├── models/
│   │   ├── timesfmForecaster.py    # Google TimesFM
│   │   ├── chronosForecaster.py    # Amazon Chronos
│   │   ├── stgnnModel.py           # Spatiotemporal GNN
│   │   └── gradientBoostingModels.py  # XGBoost + CatBoost
│   ├── ensemble/
│   │   └── stackedEnsemble.py      # Meta-learning ensemble
│   └── pipeline/
│       ├── trainingPipeline.py     # Training orchestration
│       └── predictionPipeline.py   # Inference + crisis detection
├── requirements.txt                # Python dependencies
├── run_quickstart.sh               # Quick demo script
├── run_jupyterlab.sh              # Start JupyterLab locally
└── README.md                       # This file

See MODELS.md for detailed model descriptions.
```

## Troubleshooting

### Issue: Docker build fails

```bash
# Check disk space
df -h

# Clean up Docker
docker system prune -a

# Rebuild
./scripts/build.sh
```

### Issue: kubectl can't connect to cluster

```bash
# Update kubeconfig
aws eks update-kubeconfig --name housing-ml-cluster --region us-east-1

# Verify
kubectl get nodes
```

### Issue: Pods stuck in Pending

```bash
# Check events
kubectl describe pod <pod-name> -n ml-inference

# Common issues:
# - GPU nodes not ready (wait 5 minutes)
# - Insufficient resources (scale cluster)
# - Image pull errors (check ECR permissions)
```

### Issue: Can't access ALB

```bash
# Check ingress status
kubectl get ingress -n ml-inference

# If EXTERNAL-IP is pending, wait a few minutes
# AWS takes time to provision ALB

# Alternative: Use port-forward
kubectl port-forward -n ml-inference svc/housing-crisis-jupyter 8888:8888
```

### Issue: JupyterLab asks for password

```bash
# Get token from logs
kubectl logs -n ml-inference deployment/housing-crisis-jupyter | grep "token="

# Use the full URL with token
```

## Next Steps

1. **Get Real Data**: Sign up for [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
2. **Train Models**: Run `./scripts/run-training-job.sh` with real data
3. **Customize**: Modify notebooks and configurations for your use case
4. **Scale**: Add more nodes or use HPA for autoscaling
5. **Monitor**: Set up CloudWatch logging and metrics

## Support

For model details, see `MODELS.md`.

For issues or questions, check logs:
```bash
kubectl logs -f -n ml-inference deployment/housing-crisis-jupyter
kubectl logs -f -n ml-inference deployment/housing-crisis-api
```
