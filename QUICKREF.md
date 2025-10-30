# Quick Reference Guide

## Installation

```bash
bash install.sh
```

## Get FRED API Key

https://fred.stlouisfed.org/docs/api/api_key.html

## Basic Usage

### Run Quick Start (No API Key Needed)
```bash
python notebooks/quickstart.py
```

### Run Full Pipeline
```bash
python main.py --fred-api-key YOUR_KEY --mode full --use-autogluon
```

### Train Only
```bash
python main.py --fred-api-key YOUR_KEY --mode train --target CSUSHPISA
```

## Key Parameters

| Parameter | Options | Description |
|-----------|---------|-------------|
| `--mode` | train, predict, full | Execution mode |
| `--fred-api-key` | string | FRED API key |
| `--target` | CSUSHPISA, MSPUS, etc | Target variable |
| `--use-autogluon` | flag | Enable AutoGluon |
| `--config` | path | Config file path |

## Configuration

Edit `config/config.yaml`:

```yaml
models:
  timesfm:
    maxContext: 1024      # Context window
    maxHorizon: 256       # Forecast horizon
  
  xgboost:
    nEstimators: 1000     # Number of trees
    learningRate: 0.05    # Learning rate

prediction:
  crisisThresholdHigh: 0.7    # High risk threshold
  crisisThresholdMedium: 0.4  # Medium risk threshold
```

## Data Sources

### FRED Series IDs
- `GDP`: Gross Domestic Product
- `CPIAUCSL`: Consumer Price Index
- `UNRATE`: Unemployment Rate
- `FEDFUNDS`: Federal Funds Rate
- `MORTGAGE30US`: 30-Year Mortgage Rate
- `HOUST`: Housing Starts
- `CSUSHPISA`: Case-Shiller Home Price Index
- `MSPUS`: Median Sales Price
- `USSTHPI`: US House Price Index

## Project Structure

```
src/
  data/          - Data collection & feature engineering
  models/        - TimesFM, Chronos, STGNN, XGBoost, CatBoost
  ensemble/      - Stacked ensemble & AutoGluon
  pipeline/      - Training & prediction pipelines
  utils/         - Config, graphs, visualization
```

## Python API

### Training Pipeline

```python
from pipeline.trainingPipeline import TrainingPipeline

pipeline = TrainingPipeline()
results = pipeline.runFullPipeline(
    fredApiKey="YOUR_KEY",
    targetColumn="CSUSHPISA",
    useAutoGluon=True
)
```

### Prediction Pipeline

```python
from pipeline.predictionPipeline import PredictionPipeline

predPipeline = PredictionPipeline(models=results['models'])
forecast = predPipeline.runPrediction(
    testX=testData,
    historicalY=trainData
)
```

### Individual Models

```python
from models.timesfmForecaster import TimesFMForecaster
from models.chronosForecaster import ChronosForecaster
from models.stgnnModel import STGNNForecaster
from models.gradientBoostingModels import GradientBoostingEnsemble

forecaster = TimesFMForecaster()
forecaster.compileModel()
predictions = forecaster.predictSingleSeries(timeSeries, horizon=12)

chronos = ChronosForecaster()
result = chronos.predictWithUncertainty(data, confidenceLevel=0.95)

stgnn = STGNNForecaster(numNodes=100, nodeFeatures=10)
stgnn.train(features, edges, labels, temporalLength=12)

gbEnsemble = GradientBoostingEnsemble(xgbConfig, catboostConfig)
gbEnsemble.train(trainX, trainY, valX, valY)
```

### Data Collection

```python
from data.dataCollector import DataCollector

collector = DataCollector(fredApiKey="YOUR_KEY")
data = collector.collectAllData(startDate="2010-01-01")
```

### Feature Engineering

```python
from data.featureEngineer import FeatureEngineer

engineer = FeatureEngineer()
engineeredData = engineer.engineerAllFeatures(rawData, targetColumns)
trainX, trainY, valX, valY, testX, testY = engineer.splitTimeSeriesData(
    data, targetColumn, trainRatio=0.7, valRatio=0.15
)
```

### Visualization

```python
from utils.visualizer import Visualizer

viz = Visualizer()
viz.plotTimeSeries(data, columns=['GDP', 'UNRATE'])
viz.plotPredictionsVsActual(actual, predicted)
viz.plotFeatureImportance(importance)
viz.plotCrisisTimeline(predictions, crisisScores, thresholds)
```

## Crisis Detection

### Scoring Algorithm

```python
crisisScore = (
    0.4 * priceDeclineRisk +
    0.3 * rapidAppreciationRisk +
    0.3 * volatilityIncrease
)
```

### Thresholds
- **HIGH**: crisisScore ≥ 0.7
- **MEDIUM**: 0.4 ≤ crisisScore < 0.7
- **LOW**: crisisScore < 0.4

### Policy Recommendations

**HIGH RISK:**
- Emergency rent control
- Housing voucher programs
- Fast-track approvals

**MEDIUM RISK:**
- Zoning optimization
- Development site ID
- Targeted subsidies

**LOW RISK:**
- Routine monitoring
- Model refinement
- Impact simulation

## Performance Metrics

```python
metrics = {
    'rmse': Root Mean Squared Error,
    'mae': Mean Absolute Error,
    'r2': R-Squared Score
}
```

## Troubleshooting

### FRED API Issues
```python
export FRED_API_KEY="your_key_here"
```

### GPU Not Detected
```python
import torch
print(torch.cuda.is_available())
```

### Out of Memory
- Reduce batch size in config
- Use smaller foundation models
- Enable gradient checkpointing

### Import Errors
```bash
pip install -e .
```

## Common Tasks

### Add New Economic Indicator
1. Add series ID to `dataCollector.getEconomicIndicators()`
2. Run data collection
3. Feature engineer will auto-process

### Change Forecast Horizon
```yaml
training:
  forecastHorizon: 24  # Change to 24 months
```

### Use Different Meta-Learner
```python
ensemble = StackedEnsemble(
    metaLearnerType="lasso",  # or "rf"
    metaLearnerParams={'alpha': 0.5}
)
```

### Export Model
```python
gbEnsemble.xgbForecaster.saveModel("models/saved/xgb.json")
ensemble.saveEnsemble("models/saved/ensemble.pkl")
```

### Load Pretrained Model
```python
gbEnsemble.xgbForecaster.loadModel("models/saved/xgb.json")
ensemble.loadEnsemble("models/saved/ensemble.pkl")
```

## Resources

- **FRED API Docs**: https://fred.stlouisfed.org/docs/api/
- **TimesFM GitHub**: https://github.com/google-research/timesfm
- **Chronos GitHub**: https://github.com/amazon-science/chronos-forecasting
- **PyTorch Geometric**: https://pytorch-geometric.readthedocs.io/

## Citation

```bibtex
@software{housing_crisis_ensemble_2025,
  title={Housing Crisis Prediction Ensemble},
  author={Your Name},
  year={2025},
  note={Multi-Modal Stacked Ensemble Framework}
}
```
