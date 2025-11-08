# Housing Crisis Prediction Plugin

Multi-model ensemble for real-time housing market crisis prediction and policy recommendations.

## Features

- XGBoost + CatBoost ensemble with optimized blend weights
- Automatic GPU/CPU detection
- Crisis level detection (LOW/MEDIUM/HIGH)
- Policy recommendations based on market trends
- Real-time volatility and trend analysis

## Usage

### Deploy Model

```bash
curl -X POST http://localhost:8000/deployments \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "modelName": "housingCrisis",
    "modelVersion": "1.0.0",
    "config": {
      "xgboost": {
        "nEstimators": 1000,
        "learningRate": 0.05
      },
      "catboost": {
        "iterations": 1000,
        "learningRate": 0.05
      }
    }
  }'
```

### Make Predictions

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "deploymentId": "YOUR_DEPLOYMENT_ID",
    "data": [{
      "GDP": 25000,
      "CPIAUCSL": 300,
      "UNRATE": 5.5,
      "FEDFUNDS": 4.5,
      "MORTGAGE30US": 6.5,
      "HOUST": 1400
    }],
    "options": {
      "crisisDetection": true
    }
  }'
```

## Response Format

```json
{
  "predictions": [221.5, 223.1, 224.7],
  "metadata": {
    "crisisLevel": "LOW",
    "crisisScore": 0.2,
    "recommendations": [
      "Continue routine market monitoring",
      "Refine predictive models with latest data"
    ],
    "metrics": {
      "recentTrend": 0.8,
      "volatility": 2.3
    }
  },
  "processingTimeMs": 45.2
}
```

## Requirements

- Python 3.10+
- XGBoost 2.0.0+
- CatBoost 1.2.0+
- PyTorch 2.0.0+ (optional, for GPU)
- 8GB RAM minimum
- GPU recommended for faster training
