# Plugin Development Guide

Complete guide to creating your own ML model plugins for CloudEasyML.

## Overview

CloudEasyML uses a plugin architecture that allows you to deploy any ML model with minimal code. Each plugin is a self-contained module that implements the `BaseModel` interface.

## Plugin Structure

```
plugins/yourModel/
├── __init__.py
├── model.py
├── config.yaml
├── README.md
└── requirements.txt (optional)
```

## Step-by-Step Tutorial

### 1. Create Plugin Directory

```bash
mkdir -p plugins/sentimentAnalysis
cd plugins/sentimentAnalysis
```

### 2. Create `__init__.py`

```python
from .model import SentimentAnalysisModel

__all__ = ['SentimentAnalysisModel']
```

### 3. Create `model.py`

```python
from core.modelRegistry.baseModel import (
    BaseModel, ModelMetadata, PredictionInput, PredictionOutput
)
from typing import Dict, Any
import time

class SentimentAnalysisModel(BaseModel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None

    def getMetadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="sentimentAnalysis",
            version="1.0.0",
            description="BERT-based sentiment analysis",
            author="Your Name",
            tags=["nlp", "classification", "sentiment"],
            requirements=[
                "transformers>=4.30.0",
                "torch>=2.0.0"
            ],
            gpuRequired=False,
            minMemoryGb=4,
            estimatedCostPerRequest=0.001
        )

    def load(self) -> None:
        from transformers import pipeline

        self.model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        self.isLoaded = True

    def predict(self, input: PredictionInput) -> PredictionOutput:
        if not self.isLoaded:
            raise RuntimeError("Model not loaded")

        startTime = time.time()

        texts = input.data if isinstance(input.data, list) else [input.data]
        results = self.model(texts)

        processingTime = (time.time() - startTime) * 1000

        return PredictionOutput(
            predictions=results,
            metadata={
                "modelName": "distilbert-base-uncased",
                "numInputs": len(texts)
            },
            processingTimeMs=processingTime
        )

    def train(self, trainingData: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "pre-trained model, training not required"}
```

### 4. Create `config.yaml`

```yaml
model:
  name: "distilbert-base-uncased-finetuned-sst-2-english"
  maxLength: 512
  batchSize: 32
```

### 5. Create `README.md`

```markdown
# Sentiment Analysis Plugin

BERT-based sentiment analysis for text classification.

## Usage

### Deploy

curl -X POST http://localhost:8000/deployments \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"modelName": "sentimentAnalysis", "modelVersion": "1.0.0"}'

### Predict

curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "deploymentId": "your-deployment-id",
    "data": ["This movie was amazing!", "I hated it"]
  }'

## Response

{
  "predictions": [
    {"label": "POSITIVE", "score": 0.9998},
    {"label": "NEGATIVE", "score": 0.9995}
  ],
  "metadata": {"modelName": "distilbert-base-uncased", "numInputs": 2},
  "processingTimeMs": 45.2
}
```

## BaseModel Interface

All plugins must implement these methods:

### getMetadata() -> ModelMetadata

Returns model information:

```python
ModelMetadata(
    name="modelName",
    version="1.0.0",
    description="What the model does",
    author="Your name",
    tags=["tag1", "tag2"],
    requirements=["package>=version"],
    gpuRequired=False,
    minMemoryGb=4,
    estimatedCostPerRequest=0.001
)
```

### load() -> None

Initialize and load the model:

```python
def load(self) -> None:
    self.model = loadYourModel()
    self.isLoaded = True
```

### predict(input: PredictionInput) -> PredictionOutput

Make predictions:

```python
def predict(self, input: PredictionInput) -> PredictionOutput:
    startTime = time.time()

    predictions = self.model.predict(input.data)
    options = input.options

    processingTime = (time.time() - startTime) * 1000

    return PredictionOutput(
        predictions=predictions,
        metadata={},
        processingTimeMs=processingTime
    )
```

### train(trainingData, config) -> Dict

Train or fine-tune the model:

```python
def train(self, trainingData: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    self.model.fit(trainingData['X'], trainingData['y'])

    return {
        "status": "trained",
        "metrics": {"accuracy": 0.95}
    }
```

## Advanced Features

### GPU Support

```python
import torch

def load(self) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    self.model = YourModel().to(device)
    self.isLoaded = True
```

### Custom Options

```python
def predict(self, input: PredictionInput) -> PredictionOutput:
    threshold = input.options.get('threshold', 0.5)
    topK = input.options.get('topK', 10)

    predictions = self.model.predict(input.data)
    filtered = [p for p in predictions if p['score'] > threshold][:topK]

    return PredictionOutput(predictions=filtered, ...)
```

### Batch Processing

```python
def predict(self, input: PredictionInput) -> PredictionOutput:
    batchSize = self.config.get('batchSize', 32)

    results = []
    for i in range(0, len(input.data), batchSize):
        batch = input.data[i:i + batchSize]
        batchResults = self.model.predict(batch)
        results.extend(batchResults)

    return PredictionOutput(predictions=results, ...)
```

### Model Persistence

```python
from pathlib import Path

def train(self, trainingData, config) -> Dict:
    self.model.fit(trainingData['X'], trainingData['y'])

    modelPath = Path("models") / self.getMetadata().name
    modelPath.mkdir(parents=True, exist_ok=True)

    self.model.save(modelPath / "model.pkl")

    return {"status": "trained", "savedTo": str(modelPath)}

def load(self) -> None:
    modelPath = Path("models") / self.getMetadata().name / "model.pkl"

    if modelPath.exists():
        self.model = YourModel.load(modelPath)
    else:
        self.model = YourModel()

    self.isLoaded = True
```

## Testing Your Plugin

### 1. Unit Tests

```python
import pytest
from plugins.yourModel.model import YourModel
from core.modelRegistry.baseModel import PredictionInput

def testModelLoad():
    model = YourModel({})
    model.load()
    assert model.isLoaded

def testModelPredict():
    model = YourModel({})
    model.load()

    input = PredictionInput(data=["test input"])
    output = model.predict(input)

    assert output.predictions is not None
    assert output.processingTimeMs > 0
```

### 2. Integration Test

```bash
python3 server.py

curl http://localhost:8000/models
```

### 3. Load Test

```bash
ab -n 1000 -c 10 -p request.json \
  -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/predict
```

## Best Practices

1. **Error Handling**: Catch and handle exceptions gracefully
2. **Validation**: Validate input data before processing
3. **Logging**: Use logging instead of print statements
4. **Memory**: Clean up resources in `unload()` method
5. **Documentation**: Include clear examples in README
6. **Versioning**: Use semantic versioning (major.minor.patch)
7. **Testing**: Write comprehensive tests
8. **Configuration**: Make models configurable via config.yaml

## Common Patterns

### Image Classification

```python
from PIL import Image
import numpy as np

def predict(self, input: PredictionInput) -> PredictionOutput:
    images = []
    for imgData in input.data:
        img = Image.open(imgData)
        img = self.preprocessor(img)
        images.append(img)

    batch = np.stack(images)
    predictions = self.model.predict(batch)

    return PredictionOutput(predictions=predictions.tolist(), ...)
```

### Time Series Forecasting

```python
def predict(self, input: PredictionInput) -> PredictionOutput:
    history = np.array(input.data)
    horizon = input.options.get('horizon', 12)

    forecasts = []
    for _ in range(horizon):
        nextValue = self.model.predict(history[-self.windowSize:])
        forecasts.append(nextValue)
        history = np.append(history, nextValue)

    return PredictionOutput(predictions=forecasts, ...)
```

### Text Generation

```python
def predict(self, input: PredictionInput) -> PredictionOutput:
    prompt = input.data
    maxLength = input.options.get('maxLength', 100)
    temperature = input.options.get('temperature', 0.7)

    generated = self.model.generate(
        prompt,
        maxLength=maxLength,
        temperature=temperature
    )

    return PredictionOutput(predictions=generated, ...)
```

## Publishing Your Plugin

1. Add comprehensive documentation
2. Include example usage
3. Add tests
4. Create PR to main repository
5. Update plugin registry

## Support

- Examples: See `plugins/housingCrisis/`
- Issues: GitHub Issues
- Discussions: GitHub Discussions
