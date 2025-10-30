# Housing Crisis Prediction Ensemble - Architecture

## System Overview

This system implements a state-of-the-art multi-modal stacked ensemble framework for housing crisis prediction, combining foundation models, gradient boosting, and spatiotemporal graph neural networks.

## Architecture Layers

### 1. Data Integration Layer
**Location:** `src/data/`

**Components:**
- `dataCollector.py`: Interfaces with FRED API and Zillow data sources
- `featureEngineer.py`: Advanced feature engineering with lag, rolling, and interaction features

**Data Sources:**
- Economic indicators (GDP, inflation, unemployment, interest rates)
- Housing market data (prices, inventory, sales volume)
- Demographic data (population, migration patterns)
- Geospatial data (coordinates, spatial relationships)

### 2. Base Model Layer
**Location:** `src/models/`

**Foundation Models:**
- **TimesFM** (`timesfmForecaster.py`): Google's pretrained time series foundation model
  - Zero-shot forecasting capability
  - Context length: 1024, Horizon: 256
  - Patch-based tokenization
  
- **Chronos** (`chronosForecaster.py`): Amazon's LLM-based forecasting framework
  - Chronos-Bolt for fast inference
  - Probabilistic forecasting with uncertainty quantification
  - Support for exogenous variables (ChronosX)

**Gradient Boosting Models:**
- **XGBoost** (`gradientBoostingModels.py`): GPU-accelerated gradient boosting
- **CatBoost** (`gradientBoostingModels.py`): Categorical feature handling
- **Blend Optimization**: Automated weight optimization on validation set

**Spatiotemporal Models:**
- **STGNN** (`stgnnModel.py`): Spatiotemporal Graph Neural Network
  - Spatial encoder: GraphSAGE/GCN/GAT aggregation
  - Temporal encoder: GRU-based sequence modeling
  - Attention mechanism for fusion

### 3. Ensemble Layer
**Location:** `src/ensemble/`

**Components:**
- `stackedEnsemble.py`: Meta-learning with Ridge/Lasso/RF
- `AutoGluonEnsemble`: Automated ensemble optimization

**Features:**
- Stacking with cross-validation
- Automated hyperparameter tuning
- Model weight extraction
- Performance comparison across base models

### 4. Prediction & Crisis Detection Layer
**Location:** `src/pipeline/`

**Components:**
- `predictionPipeline.py`: Forecast generation and crisis detection
- `crisisDetector.py`: Multi-factor crisis scoring algorithm

**Crisis Detection Methodology:**
- Price decline risk assessment
- Rapid appreciation risk monitoring
- Volatility increase tracking
- Multi-threshold classification (High/Medium/Low)

**Policy Recommendation Engine:**
- Emergency interventions (crisis probability > 0.7)
- Preventive measures (0.4 - 0.7)
- Optimization strategies (< 0.4)

### 5. Utilities Layer
**Location:** `src/utils/`

**Components:**
- `configLoader.py`: YAML configuration management
- `graphBuilder.py`: Spatial and temporal graph construction
- `visualizer.py`: Advanced visualization toolkit

## Data Flow

```
Raw Data (FRED, Zillow)
    ↓
Feature Engineering (Lag, Rolling, Interactions)
    ↓
Train/Val/Test Split (Time-based)
    ↓
Base Models Training (TimesFM, Chronos, XGBoost, CatBoost, STGNN)
    ↓
Meta-Learner Training (Stacked Ensemble / AutoGluon)
    ↓
Prediction Generation
    ↓
Crisis Detection & Scoring
    ↓
Policy Recommendations
```

## Model Training Strategy

### TimesFM & Chronos
- Pretrained foundation models (zero-shot)
- No fine-tuning required
- Direct inference on processed time series

### Gradient Boosting
- Supervised training on engineered features
- Early stopping with validation set
- Blend weight optimization

### STGNN
- Graph construction from spatial coordinates or economic similarity
- Supervised training with MSE loss
- Adam optimizer with weight decay

### Meta-Learner
- Trained on base model predictions (out-of-fold)
- Ridge regression for stability
- Optional: AutoGluon for automated optimization

## Configuration

**File:** `config/config.yaml`

**Sections:**
- `data`: Data paths and caching
- `models`: Model-specific hyperparameters
- `ensemble`: Meta-learner configuration
- `training`: Training parameters
- `prediction`: Crisis thresholds

## Performance Targets

| Metric | Target |
|--------|--------|
| Housing Price R² | > 0.93 |
| Crisis Forecasting Accuracy | > 90% |
| Forecast Horizon | 12-18 months |
| Inference Latency | < 100ms |

## Extensibility

### Adding New Base Models
1. Create model class in `src/models/`
2. Implement `train()` and `predict()` methods
3. Register in `trainingPipeline.py`
4. Add configuration in `config.yaml`

### Adding New Data Sources
1. Extend `dataCollector.py` with new API client
2. Update feature engineering pipeline
3. Add data source configuration

### Custom Crisis Detection Logic
1. Modify `crisisDetector.py` scoring algorithm
2. Add new risk factors
3. Update recommendation rules

## Dependencies

**Core:**
- PyTorch 2.0+ (Deep learning framework)
- PyTorch Geometric (Graph neural networks)
- XGBoost, CatBoost (Gradient boosting)
- scikit-learn (Preprocessing, metrics)

**Foundation Models:**
- TimesFM (Google Research)
- Chronos (Amazon Science)

**Optional:**
- AutoGluon (Automated ML)

**Data:**
- fredapi (FRED API client)
- pandas, numpy (Data manipulation)

**Visualization:**
- matplotlib, seaborn, plotly

## Deployment Considerations

### Production Deployment
- Containerize with Docker
- Orchestrate with Kubernetes
- Expose REST API endpoints
- Implement model versioning
- Add monitoring and alerting

### Privacy & Security
- Consider federated learning for multi-region deployment
- Implement differential privacy for sensitive data
- Secure API key management
- Data encryption at rest and in transit

### Scalability
- Batch prediction for efficiency
- Model caching and versioning
- Distributed training for large-scale data
- GPU acceleration for deep learning models
