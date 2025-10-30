# Models Reference

## Foundation Models (Time Series)

### TimesFM 2.5 (Google Research)
Pretrained transformer-based foundation model for zero-shot time series forecasting with patching mechanism.

### Chronos-Bolt (Amazon Science)
LLM-based probabilistic forecasting framework with 250x faster inference and uncertainty quantification.

## Gradient Boosting Models

### XGBoost
GPU-accelerated gradient boosting with tree-based learning for structured feature prediction.

### CatBoost
Ordered boosting algorithm with native categorical feature support and symmetric tree structure.

### Gradient Boosting Ensemble
Automated blend of XGBoost and CatBoost with validation-based weight optimization.

## Deep Learning Models

### STGNN (Spatiotemporal Graph Neural Network)
Custom GNN combining GraphSAGE spatial aggregation, GRU temporal encoding, and attention-based fusion.

### Spatial Encoder
Graph convolutional network (GCN/GraphSAGE/GAT) for capturing spatial dependencies between regions.

### Temporal Encoder
Recurrent neural network (GRU) for modeling temporal patterns in time series data.

## Meta-Learning Models

### Stacked Ensemble
Ridge/Lasso/Random Forest meta-learner trained on base model predictions for optimal ensemble weighting.

### AutoGluon Ensemble
Automated machine learning framework for ensemble optimization with neural architecture search.

## Utility Models

### Feature Engineer
Statistical feature transformation pipeline with lag, rolling, difference, and interaction terms.

### Crisis Detector
Multi-factor scoring algorithm combining price risk, appreciation risk, and volatility metrics.

## Model Summary Table

| Model | Type | Purpose | Key Feature |
|-------|------|---------|-------------|
| TimesFM 2.5 | Foundation | Temporal forecasting | Zero-shot, 1024 context |
| Chronos-Bolt | Foundation | Probabilistic forecast | 250x faster, uncertainty |
| XGBoost | Gradient Boosting | Feature-based prediction | GPU acceleration |
| CatBoost | Gradient Boosting | Categorical handling | Ordered boosting |
| STGNN | Deep Learning | Spatiotemporal modeling | Graph + sequence fusion |
| Stacked Ensemble | Meta-Learning | Ensemble optimization | Cross-validated stacking |
| AutoGluon | AutoML | Automated optimization | Neural architecture search |

## Model Pipeline

```
Input Data
    ↓
TimesFM → Temporal patterns (foundation model)
Chronos → Probabilistic forecast (foundation model)
XGBoost → Feature-based prediction (gradient boosting)
CatBoost → Categorical features (gradient boosting)
STGNN → Spatial-temporal dynamics (graph neural network)
    ↓
Stacked Meta-Learner (Ridge/Lasso/RF)
    ↓
Final Ensemble Prediction
    ↓
Crisis Detection & Policy Recommendations
```

## Model Weights & Sizes

| Model | Parameters | GPU Memory | Inference Time |
|-------|-----------|------------|----------------|
| TimesFM 2.5 | 200M | ~2GB | ~50ms |
| Chronos-Bolt | 20-250M | ~1-3GB | ~20ms |
| XGBoost | ~10K trees | ~500MB | ~5ms |
| CatBoost | ~10K trees | ~500MB | ~5ms |
| STGNN | ~5M | ~1GB | ~10ms |

## Training vs Inference

### Zero-Shot (No Training)
- TimesFM 2.5
- Chronos-Bolt

### Requires Training
- XGBoost
- CatBoost
- STGNN
- Stacked Ensemble
- AutoGluon

## GPU Requirements

### Recommended
- NVIDIA GPU with 8GB+ VRAM
- CUDA 12.1+
- PyTorch 2.0+

### Minimum
- NVIDIA GPU with 4GB+ VRAM
- CUDA 11.8+
- PyTorch 2.0+

### CPU Fallback
All models support CPU inference with degraded performance (10-50x slower).
