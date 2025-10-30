# Deployment Architecture Notes

## Lambda + GPU Architecture Clarification

### The Challenge
AWS Lambda **does not support GPU directly**. Lambda runs on CPU-only instances, making it unsuitable for GPU-intensive ML inference.

### The Solution: Lambda → EKS Pattern

```
┌──────────────┐         ┌─────────────────┐         ┌──────────────┐
│              │         │                 │         │              │
│  API Gateway │────────▶│  Lambda         │────────▶│  EKS Cluster │
│              │         │  (Trigger)      │         │  (GPU Nodes) │
│              │         │                 │         │              │
└──────────────┘         └─────────────────┘         └──────────────┘
                                                             │
                                                             │
                                                      ┌──────▼──────┐
                                                      │   Training  │
                                                      │   Job with  │
                                                      │   GPU       │
                                                      └─────────────┘
```

### How It Works

#### For Training Jobs
1. **Lambda receives trigger** (API Gateway, EventBridge, S3 event)
2. **Lambda creates Kubernetes Job manifest**
3. **Lambda submits job to EKS** (via Kubernetes API)
4. **EKS schedules job on GPU node** (g5.2xlarge)
5. **Training runs with CUDA acceleration**
6. **Models saved to EFS/S3**

#### For Inference
**Option 1: Lambda → EKS Service (Recommended)**
```python
Lambda → HTTP request → EKS Inference Service (GPU) → Response
```
- Lambda acts as orchestrator/router
- Actual inference runs on GPU pods
- Low latency (~50-100ms inference + network)

**Option 2: Direct EKS Ingress**
```python
API Gateway → ALB Ingress → EKS Inference Service (GPU)
```
- Bypasses Lambda entirely
- Lowest latency possible
- Better for high-throughput

**Option 3: SageMaker Real-Time Inference**
```python
Lambda → SageMaker Endpoint (GPU) → Response
```
- Managed GPU inference
- Higher cost but fully managed
- Auto-scaling built-in

## Deployment Patterns

### Pattern 1: Cost-Optimized (Batch)
**Use Case:** Nightly retraining, bulk predictions

**Setup:**
- Training: EKS Job on Spot g5.2xlarge
- Inference: CPU-based Lambda for simple queries
- GPU inference: On-demand for complex batches

**Cost:** ~$800/month (60% savings)

### Pattern 2: Low-Latency (Real-Time)
**Use Case:** Live dashboard, API service

**Setup:**
- Inference: 2x g5.xlarge always-on
- Training: Scheduled weekly on Spot
- Lambda: Trigger and orchestration only

**Cost:** ~$1,500/month

### Pattern 3: Hybrid (Recommended)
**Use Case:** Production service with batch updates

**Setup:**
- Inference: 1-2x g5.xlarge with autoscaling
- Training: On-demand Spot instances
- Lambda: Smart routing (simple → CPU, complex → GPU)

**Cost:** ~$1,200/month

## Docker Image Optimization

### Current Approach (Follows Your Pattern)
```dockerfile
# Stage 1: Base (CUDA + Conda + Python)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
→ Install conda, AWS CLI, base packages

# Stage 2: ML Dependencies
→ Install PyTorch, XGBoost, CatBoost
→ Install foundation models (TimesFM, Chronos)

# Stage 3: Application
→ Copy source code
→ Install application
```

### Why This Structure?
1. **Layer Caching**: Base image rarely changes
2. **Faster Builds**: ML deps cached separately
3. **Multi-Use**: Same base for different apps
4. **Size Control**: Only add what's needed per stage

### Image Sizes
- Base: ~5GB (CUDA + conda)
- ML: ~12GB (+ PyTorch, models)
- Final: ~12.5GB (+ application code)

## Version Management Strategy

### Approach 1: SemVer Tags
```bash
export IMAGE_TAG=v1.2.3
./scripts/build.sh
./scripts/push.sh
```

**Images:**
- `housing-crisis-ml:v1.2.3`
- `housing-crisis-ml:v1.2`
- `housing-crisis-ml:v1`
- `housing-crisis-ml:latest`

### Approach 2: Git-Based
```bash
export IMAGE_TAG=$(git rev-parse --short HEAD)
```

**Images:**
- `housing-crisis-ml:abc123f`
- `housing-crisis-ml:main-abc123f`

### Approach 3: Date-Based
```bash
export IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
```

**Images:**
- `housing-crisis-ml:20250130-143022`

## Kubernetes Node Selection

### GPU Node Types (AWS g5 family)

| Instance | GPU | vCPU | Memory | GPU Mem | $/hour | Use Case |
|----------|-----|------|--------|---------|--------|----------|
| g5.xlarge | 1x A10G | 4 | 16 GB | 24 GB | $1.006 | Inference |
| g5.2xlarge | 1x A10G | 8 | 32 GB | 24 GB | $1.212 | Training |
| g5.4xlarge | 1x A10G | 16 | 64 GB | 24 GB | $1.624 | Large models |
| g5.12xlarge | 4x A10G | 48 | 192 GB | 96 GB | $5.672 | Multi-GPU |

### Our Recommendations

**Inference Pods:**
- **Node**: g5.xlarge (1 GPU, 16GB RAM)
- **Pods**: 1 pod per node (full GPU dedicated)
- **Scaling**: 2-10 pods based on traffic

**Training Jobs:**
- **Node**: g5.2xlarge (1 GPU, 32GB RAM)
- **Spot**: Yes (60% cost savings)
- **Scaling**: 0-5 nodes (start on-demand)

## EFS vs EBS vs S3

### EFS (Shared Storage) - Current Choice
**Pros:**
- Multi-pod access (ReadWriteMany)
- Dynamic resizing
- Regional availability
- Perfect for model sharing

**Cons:**
- Higher cost ($0.30/GB/month)
- Slightly slower than EBS
- Requires VPC setup

**Use For:**
- Model storage (shared across pods)
- Training data cache
- Shared checkpoints

### EBS (Block Storage)
**Pros:**
- Faster than EFS
- Lower cost ($0.10/GB/month)
- Direct attach

**Cons:**
- Single pod only (ReadWriteOnce)
- AZ-specific
- Manual sizing

**Use For:**
- Jupyter workspace (single user)
- Temporary training storage
- Individual pod caches

### S3 (Object Storage)
**Pros:**
- Lowest cost ($0.023/GB/month)
- Unlimited scale
- Versioning

**Cons:**
- Slower access
- Requires mounting (s3fs/Mountpoint)
- Not POSIX-compliant

**Use For:**
- Model archives
- Dataset storage
- Backup/versioning

## Monitoring & Observability

### GPU Metrics
```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/dcgm-exporter/main/dcgm-exporter.yaml
```

**Metrics Collected:**
- GPU utilization %
- GPU memory used
- GPU temperature
- Power consumption
- SM clock speed

### Application Metrics

**FastAPI Server:**
- Request latency (p50, p95, p99)
- Requests per second
- Error rate
- Model load time

**Training Jobs:**
- Training loss
- Validation accuracy
- Epoch duration
- GPU utilization

### Recommended Stack

**Basic (Free):**
- CloudWatch Container Insights
- EKS control plane logs
- kubectl top nodes/pods

**Advanced (Cost: ~$50/month):**
- Prometheus + Grafana
- DCGM Exporter for GPU
- Loki for log aggregation
- Tempo for tracing

**Enterprise:**
- DataDog ($15/host/month)
- New Relic
- Splunk

## Security Best Practices

### 1. Image Scanning
```bash
aws ecr put-image-scanning-configuration \
  --repository-name housing-crisis-ml \
  --image-scanning-configuration scanOnPush=true
```

### 2. Network Policies
- Isolate inference pods from training
- Restrict egress to known endpoints
- Use service mesh (Istio/Linkerd)

### 3. Secrets Management
```bash
kubectl create secret generic fred-api-key \
  --from-literal=key=$FRED_API_KEY \
  -n ml-jobs
```

### 4. RBAC
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ml-inference
  name: model-reader
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

## Troubleshooting Common Issues

### 1. Pod Stuck in Pending (GPU not available)
```bash
kubectl describe pod <pod-name> -n ml-inference

# Check:
- Node selector matches GPU nodes?
- GPU resources requested correctly?
- NVIDIA device plugin running?
```

### 2. OOM Killed
```bash
# Increase memory limits
resources:
  limits:
    memory: "32Gi"  # Increase from 16Gi
```

### 3. Slow Model Loading
```bash
# Use EBS instead of EFS for single-pod workloads
# Or increase EFS throughput mode to "provisioned"
```

### 4. High Costs
```bash
# Enable Spot instances
# Scale down during off-hours
# Use smaller GPU instances (g5.xlarge)
# Implement request-based autoscaling
```

## Next Steps

1. **Test Locally**: Use `docker-compose` for local testing
2. **Stage Environment**: Deploy to small EKS cluster first
3. **Load Testing**: Use Locust/k6 for performance testing
4. **Cost Monitoring**: Set up AWS Cost Anomaly Detection
5. **CI/CD**: GitHub Actions → ECR → EKS deployment
