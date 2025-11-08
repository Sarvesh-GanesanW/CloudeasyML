# CloudEasyML Architecture

Complete technical overview of the CloudEasyML platform architecture.

## Overview

CloudEasyML is a multi-tenant SaaS platform for deploying ML models with built-in authentication, billing, and cloud deployment capabilities. The architecture is designed to be:

- **Extensible**: Plugin-based model system
- **Scalable**: Kubernetes-native with auto-scaling
- **Secure**: API key authentication and multi-tenant isolation
- **Observable**: Built-in usage tracking and monitoring

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                    (ALB/GCE/Azure LB)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Server                            │ │
│  │  - REST endpoints                                       │ │
│  │  - Authentication middleware                            │ │
│  │  - Request routing                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────┬──────────────┬─────────────┬─────────────┐ │
│  │   Auth      │   Billing    │  Database   │   Model     │ │
│  │   System    │   Engine     │  Manager    │  Registry   │ │
│  └─────────────┴──────────────┴─────────────┴─────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Plugin Models                          │ │
│  │  ┌─────────────┬─────────────┬─────────────────────┐  │ │
│  │  │ Housing     │  Custom     │     Custom          │  │ │
│  │  │ Crisis      │  Model 1    │     Model N         │  │ │
│  │  └─────────────┴─────────────┴─────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                         │
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Persistent Storage                          │
│  - User data (JSON/PostgreSQL)                              │
│  - API keys                                                  │
│  - Deployments                                               │
│  - Usage records                                             │
│  - Trained models                                            │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Server (`core/api/apiServer.py`)

FastAPI-based REST API server that handles all HTTP requests.

**Responsibilities:**
- Route management
- Request validation
- Response formatting
- CORS handling
- Error handling

**Key Endpoints:**
- `GET /health` - Health check
- `GET /models` - List available models
- `POST /deployments` - Create deployment
- `POST /predict` - Make predictions
- `POST /api-keys` - Generate API keys
- `GET /usage` - Get usage statistics

### 2. Authentication System (`core/auth/`)

**Components:**
- `apiKeyManager.py` - API key generation and validation
- `authMiddleware.py` - FastAPI authentication middleware

**Flow:**
```
Request → Extract Bearer Token → Validate Key → Check Rate Limit → Allow/Deny
```

**Features:**
- Secure key generation (SHA-256 hashing)
- Expiration support
- Per-key rate limiting
- Permission-based access control

### 3. Model Registry (`core/modelRegistry/`)

**Components:**
- `baseModel.py` - Abstract base class for all models
- `modelManager.py` - Plugin discovery and lifecycle management

**Plugin Discovery Flow:**
```
1. Scan plugins/ directory
2. Import model.py from each plugin
3. Find classes inheriting from BaseModel
4. Register model in registry
5. Ready for deployment
```

**Model Lifecycle:**
```
Register → Load → Predict → Unload
```

### 4. Billing Engine (`core/billing/`)

**Components:**
- `pricingEngine.py` - Cost calculation
- `usageTracker.py` - Request tracking and aggregation

**Pricing Model:**
```python
cost = (perRequest * requestCount) +
       (perSecond * processingTime) +
       (perGpuHour * gpuTime)
```

**Usage Tracking:**
- Per-request tracking
- Aggregated by user
- Aggregated by model
- Time-based queries

### 5. Database Layer (`core/database/`)

**Components:**
- `databaseManager.py` - Data persistence
- `models.py` - Pydantic schemas

**Current Implementation:**
- JSON file-based storage
- Production-ready interfaces for:
  - PostgreSQL
  - MongoDB
  - Redis

**Data Models:**
- User
- ApiKey
- Deployment
- UsageRecord

## Plugin System

### Plugin Structure

```
plugins/yourModel/
├── __init__.py          # Export model class
├── model.py             # Model implementation
├── config.yaml          # Default configuration
├── README.md            # Documentation
└── requirements.txt     # Dependencies (optional)
```

### BaseModel Interface

Every plugin must implement:

```python
class BaseModel(ABC):
    @abstractmethod
    def getMetadata(self) -> ModelMetadata

    @abstractmethod
    def load(self) -> None

    @abstractmethod
    def predict(self, input: PredictionInput) -> PredictionOutput

    @abstractmethod
    def train(self, trainingData: Any, config: Dict) -> Dict
```

### Plugin Loading

```python
modelManager = ModelManager("plugins")
modelManager.loadAllPlugins()

models = modelManager.listModels()

model = modelManager.getModel("housingCrisis", config)

result = model.predict(input)
```

## Request Flow

### 1. Prediction Request

```
1. Client sends POST /predict with Bearer token
   ↓
2. AuthMiddleware extracts and validates API key
   ↓
3. Check rate limit for key
   ↓
4. Retrieve deployment configuration
   ↓
5. ModelManager loads model (if not cached)
   ↓
6. Model processes input and returns predictions
   ↓
7. UsageTracker records request metadata
   ↓
8. API returns predictions to client
```

### 2. Model Deployment Request

```
1. Client sends POST /deployments
   ↓
2. Validate API key
   ↓
3. Check if model exists in registry
   ↓
4. Create deployment record
   ↓
5. Generate deployment ID
   ↓
6. Return deployment metadata
```

## Data Flow

### Authentication Flow

```
┌──────────┐    1. Request      ┌─────────────┐
│  Client  │ ──────────────────→│ API Server  │
└──────────┘                     └──────┬──────┘
                                        │
                                        │ 2. Extract token
                                        ↓
                                 ┌─────────────┐
                                 │ Auth        │
                                 │ Middleware  │
                                 └──────┬──────┘
                                        │
                                        │ 3. Validate
                                        ↓
                                 ┌─────────────┐
                                 │ API Key     │
                                 │ Manager     │
                                 └──────┬──────┘
                                        │
                                        │ 4. Lookup
                                        ↓
                                 ┌─────────────┐
                                 │ Database    │
                                 └─────────────┘
```

### Prediction Flow

```
┌──────────┐                    ┌─────────────┐
│  Client  │───── Predict ─────→│ API Server  │
└──────────┘                     └──────┬──────┘
     ↑                                  │
     │                                  ↓
     │                           ┌─────────────┐
     │                           │ Model       │
     │                           │ Manager     │
     │                           └──────┬──────┘
     │                                  │
     │                                  ↓
     │                           ┌─────────────┐      ┌─────────────┐
     │                           │ Plugin      │─────→│ GPU/CPU     │
     │                           │ Model       │←─────│ Resources   │
     │                           └──────┬──────┘      └─────────────┘
     │                                  │
     │                                  ↓
     │                           ┌─────────────┐
     │                           │ Usage       │
     │                           │ Tracker     │
     │                           └──────┬──────┘
     │                                  │
     └──────── Response ────────────────┘
```

## Deployment Architecture

### Kubernetes Deployment

```
┌──────────────────────────────────────────────────────┐
│                  Ingress/ALB                          │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────────┐
│                   Service (LoadBalancer)              │
└───────────────────────┬──────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────┴────────┐              ┌───────┴────────┐
│   Pod 1        │              │   Pod 2        │
│ ┌────────────┐ │              │ ┌────────────┐ │
│ │ API Server │ │              │ │ API Server │ │
│ └────────────┘ │              │ └────────────┘ │
│ ┌────────────┐ │              │ ┌────────────┐ │
│ │ GPU Model  │ │              │ │ GPU Model  │ │
│ └────────────┘ │              │ └────────────┘ │
└────────┬───────┘              └────────┬───────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                ┌────────┴────────┐
                │ Persistent      │
                │ Volume          │
                │ - Database      │
                │ - Models        │
                └─────────────────┘
```

### Resource Allocation

**Development:**
- 1 pod
- 4 CPU cores
- 8GB RAM
- Optional GPU

**Production:**
- 2-10 pods (auto-scaling)
- 4-8 CPU cores per pod
- 16-32GB RAM per pod
- 1 GPU per pod (g5.xlarge/T4/V100)

## Security Architecture

### Multi-Tenant Isolation

```
User A ──→ API Key A ──→ Deployment A ──→ Model Instance A
User B ──→ API Key B ──→ Deployment B ──→ Model Instance B
```

**Isolation Levels:**
1. API Key validation per request
2. Deployment ownership verification
3. Usage tracking per user
4. Rate limiting per key

### API Key Security

```
Generation:
keyId = "sk_" + random(16)
secret = random(32)
fullKey = keyId + "." + secret
keyHash = SHA256(secret)

Storage:
{keyId: ..., keyHash: ..., userId: ...}

Validation:
receivedKey = request.headers["Authorization"]
keyId, secret = receivedKey.split(".")
computedHash = SHA256(secret)
return computedHash == storedHash
```

## Monitoring & Observability

### Health Checks

```
GET /health
{
  "status": "healthy",
  "timestamp": "2025-11-08T12:00:00",
  "modelsLoaded": 3
}
```

### Usage Metrics

```
GET /usage
{
  "userId": "user123",
  "totalCost": 45.67,
  "totalRequests": 10000,
  "byModel": {
    "housingCrisis": {
      "requests": 8000,
      "cost": 36.54,
      "processingTimeMs": 123456
    }
  }
}
```

### Logging

- Request/response logging
- Error tracking
- Performance metrics
- Cost tracking

## Scalability

### Horizontal Scaling

**API Server:**
- Stateless design
- Load balanced across pods
- Auto-scaling based on CPU/memory

**Model Instances:**
- Lazy loading (load on first use)
- In-memory caching
- Shared model weights across requests

### Vertical Scaling

**GPU Resources:**
- Automatic GPU detection
- Fallback to CPU
- Batch processing support

## Performance Optimization

### Model Caching

```python
loadedModels = {
    "housingCrisis": modelInstance,
    "sentimentAnalysis": modelInstance
}

if modelName not in loadedModels:
    loadedModels[modelName] = loadModel(modelName)
```

### Request Batching

```python
async def predictBatch(requests):
    batch = [r.data for r in requests]
    results = model.predict(batch)
    return results
```

### GPU Optimization

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
```

## Extension Points

### Custom Database

```python
class PostgresDatabase(DatabaseManager):
    def __init__(self, connectionString):
        self.conn = psycopg2.connect(connectionString)

    def saveUser(self, user):
        ...
```

### Custom Pricing

```python
class CustomPricingEngine(PricingEngine):
    def calculateCost(self, ...):
        baseCost = super().calculateCost(...)
        return baseCost * userTierMultiplier
```

### Custom Auth

```python
class OAuth2Middleware(AuthMiddleware):
    async def authenticate(self, token):
        return validateOAuth2Token(token)
```

## Future Enhancements

1. **A/B Testing**: Deploy multiple model versions
2. **Model Versioning**: Track and rollback versions
3. **Batch Inference**: Queue-based batch processing
4. **Model Marketplace**: Public model sharing
5. **Webhooks**: Event-driven notifications
6. **Metrics Export**: Prometheus/Grafana integration
7. **Multi-Region**: Global deployment
8. **Edge Deployment**: CDN-based inference

## References

- FastAPI: https://fastapi.tiangolo.com
- Pydantic: https://docs.pydantic.dev
- Kubernetes: https://kubernetes.io
- PyTorch: https://pytorch.org
