# CloudEasyML

Open-source SaaS platform for plug-and-play ML model deployment. Deploy any ML model with authentication, billing, monitoring, and multi-cloud support out of the box.

## Features

- **Plugin Architecture**: Drop in any ML model with a simple interface
- **Multi-Tenant**: Built-in user management and API key authentication
- **Usage Tracking**: Automatic billing and cost tracking per request
- **Auto-Scaling**: Deploy to AWS, GCP, or Azure with one command
- **GPU Support**: Automatic GPU/CPU detection and optimization
- **REST API**: Production-ready FastAPI backend
- **Admin Dashboard**: Beautiful web UI for model management
- **Example Models**: Housing Crisis prediction included as reference

## Quick Start

```bash
git clone https://github.com/yourusername/CloudEasyML.git
cd CloudEasyML

pip install -r requirements.txt

python3 server.py
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Architecture

```
CloudEasyML/
├── core/                    # Platform core
│   ├── auth/               # API key management
│   ├── billing/            # Usage tracking & pricing
│   ├── database/           # Multi-tenant data layer
│   ├── modelRegistry/      # Plugin system
│   └── api/                # REST API server
├── plugins/                # Model plugins
│   └── housingCrisis/      # Example: Housing market prediction
├── admin/                  # Web dashboard
└── deploy/                 # Cloud deployment configs
```

## Creating a Plugin

Create a new model plugin in 3 steps:

### 1. Create plugin directory

```bash
mkdir -p plugins/myModel
touch plugins/myModel/__init__.py
touch plugins/myModel/model.py
```

### 2. Implement BaseModel interface

```python
from core.modelRegistry.baseModel import BaseModel, ModelMetadata, PredictionInput, PredictionOutput

class MyModel(BaseModel):
    def getMetadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="myModel",
            version="1.0.0",
            description="My awesome model",
            author="Your Name",
            tags=["classification", "nlp"],
            gpuRequired=False,
            minMemoryGb=4
        )

    def load(self) -> None:
        self.isLoaded = True

    def predict(self, input: PredictionInput) -> PredictionOutput:
        import time
        startTime = time.time()

        predictions = []

        processingTime = (time.time() - startTime) * 1000

        return PredictionOutput(
            predictions=predictions,
            metadata={},
            processingTimeMs=processingTime
        )

    def train(self, trainingData, config) -> dict:
        return {"status": "trained"}
```

### 3. Deploy your model

```bash
python3 server.py
```

Your model is now available at `http://localhost:8000/models`

## API Usage

### 1. Create API Key

```bash
curl -X POST "http://localhost:8000/api-keys?userId=user123" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Key", "rateLimit": 1000}'
```

Response:
```json
{
  "apiKey": "sk_abc123.xyz789",
  "warning": "Save this key securely. It won't be shown again."
}
```

### 2. Create Deployment

```bash
curl -X POST http://localhost:8000/deployments \
  -H "Authorization: Bearer sk_abc123.xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "modelName": "housingCrisis",
    "modelVersion": "1.0.0",
    "config": {
      "xgboost": {"nEstimators": 1000},
      "catboost": {"iterations": 1000}
    }
  }'
```

### 3. Make Predictions

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer sk_abc123.xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "deploymentId": "deployment-uuid",
    "data": [{"feature1": 100, "feature2": 200}],
    "options": {"crisisDetection": true}
  }'
```

### 4. Check Usage & Billing

```bash
curl http://localhost:8000/usage \
  -H "Authorization: Bearer sk_abc123.xyz789"
```

Response:
```json
{
  "userId": "user123",
  "totalCost": 1.45,
  "totalRequests": 1250,
  "byModel": {
    "housingCrisis": {
      "requests": 1250,
      "cost": 1.45,
      "processingTimeMs": 56789
    }
  }
}
```

## Example Plugin: Housing Crisis Prediction

The platform includes a complete example: multi-model ensemble for housing market crisis prediction.

### Features
- XGBoost + CatBoost ensemble
- Crisis level detection (LOW/MEDIUM/HIGH)
- Policy recommendations
- Automatic GPU acceleration

### Usage

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "deploymentId": "your-deployment",
    "data": [{
      "GDP": 25000,
      "UNRATE": 5.5,
      "FEDFUNDS": 4.5
    }],
    "options": {"crisisDetection": true}
  }'
```

See `plugins/housingCrisis/README.md` for full documentation.

## Cloud Deployment

### AWS (EKS)

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

./deploy/aws/deploy.sh
```

### GCP (GKE)

```bash
export GCP_PROJECT=my-project
export GCP_REGION=us-central1

./deploy/gcp/deploy.sh
```

### Azure (AKS)

```bash
export AZURE_RESOURCE_GROUP=cloudeasyml
export AZURE_LOCATION=eastus

./deploy/azure/deploy.sh
```

## Development

### Project Structure

```
core/
├── auth/
│   ├── apiKeyManager.py       # API key generation & validation
│   └── authMiddleware.py      # FastAPI authentication
├── billing/
│   ├── usageTracker.py        # Request tracking
│   └── pricingEngine.py       # Cost calculation
├── database/
│   ├── databaseManager.py     # Data persistence
│   └── models.py              # Database schemas
├── modelRegistry/
│   ├── baseModel.py           # Plugin interface
│   └── modelManager.py        # Plugin discovery & loading
└── api/
    └── apiServer.py           # FastAPI application
```

### Code Style

- camelCase for variables and functions
- PascalCase for classes
- No comments in code
- Type hints required
- Pydantic for validation

### Testing

```bash
pytest tests/
```

## Configuration

Edit `config/config.yaml`:

```yaml
models:
  xgboost:
    nEstimators: 1000
    learningRate: 0.05

  catboost:
    iterations: 1000
    learningRate: 0.05

pricing:
  default:
    perRequest: 0.001
    perSecond: 0.0001
    perGpuHour: 0.5
```

## Admin Dashboard

Access the web dashboard at `http://localhost:8000/admin`:

- View all deployed models
- Generate API keys
- Monitor usage statistics
- Check platform health

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### List Models

```bash
curl http://localhost:8000/models
```

### View Deployments

```bash
curl http://localhost:8000/deployments \
  -H "Authorization: Bearer YOUR_KEY"
```

## Contributing

1. Fork the repository
2. Create your plugin in `plugins/yourModel/`
3. Add tests in `tests/plugins/test_yourModel.py`
4. Submit a pull request

### Plugin Guidelines

- Inherit from `BaseModel`
- Implement all required methods
- Include `config.yaml` with defaults
- Add `README.md` with usage examples
- Support both GPU and CPU
- Include metadata with cost estimates

## License

MIT License - see LICENSE file for details

## Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Examples: `/plugins`

## Roadmap

- [ ] PostgreSQL/MongoDB database support
- [ ] Kubernetes autoscaling
- [ ] Model versioning
- [ ] A/B testing framework
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Stripe integration
- [ ] Model marketplace
- [ ] Webhook notifications
- [ ] Batch inference

## Examples

See `plugins/` directory for complete examples:

- `housingCrisis/` - Time series forecasting with ensemble models
- More coming soon!

## Cost Breakdown

### Self-Hosted (Free)
- Run on your infrastructure
- No platform fees
- Pay only for compute

### AWS Deployment
- EKS Control Plane: $73/month
- 2x g5.xlarge GPU nodes: $1,460/month (or $584 with spot)
- ALB: $23/month
- Total: ~$600-1,600/month

### Usage-Based Pricing
Configure in `core/billing/pricingEngine.py`:

```python
pricingConfig = {
    'default': {
        'perRequest': 0.001,
        'perSecond': 0.0001,
        'perGpuHour': 0.5
    }
}
```

## Security

- API key authentication required
- Rate limiting per key
- Multi-tenant data isolation
- No credentials in code
- Environment-based configuration

## Performance

- Automatic GPU detection
- Model caching
- Async request handling
- Connection pooling
- Response compression

---

Made with ❤️ by the CloudEasyML team
