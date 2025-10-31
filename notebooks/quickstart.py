import sys
from pathlib import Path

projectRoot = Path(__file__).parent.parent
sys.path.append(str(projectRoot / "src"))

import pandas as pd
import numpy as np
from pipeline.trainingPipeline import TrainingPipeline
from pipeline.predictionPipeline import PredictionPipeline

print("Housing Crisis Prediction System - Quick Start Example")
print("=" * 70)

fredApiKey = None

print("\nNOTE: For full functionality, set your FRED API key:")
print("fredApiKey = 'your_fred_api_key_here'")
print("\nWithout API key, the system will use cached/demo data if available.\n")

configPath = str(projectRoot / "config" / "config.yaml")
pipeline = TrainingPipeline(configPath=configPath)

print("Initializing data collector...")
pipeline.initializeDataCollector(fredApiKey=fredApiKey)

print("\nGenerating synthetic demo data for quick start...")

dates = pd.date_range(start="2010-01-01", end="2024-12-31", freq="MS")
n = len(dates)

syntheticData = pd.DataFrame(
    {
        "GDP": np.cumsum(np.random.randn(n) * 100 + 50) + 15000,
        "CPIAUCSL": np.cumsum(np.random.randn(n) * 0.5 + 0.2) + 220,
        "UNRATE": np.clip(np.random.randn(n) * 1.5 + 5.5, 3, 10),
        "FEDFUNDS": np.clip(np.random.randn(n) * 0.5 + 2.5, 0, 6),
        "MORTGAGE30US": np.clip(np.random.randn(n) * 0.8 + 4.5, 2.5, 8),
        "HOUST": np.abs(np.random.randn(n) * 200 + 1200),
        "CSUSHPISA": np.cumsum(np.random.randn(n) * 2 + 0.5) + 150,
    },
    index=dates,
)

print(f"Synthetic data shape: {syntheticData.shape}")
print(f"Date range: {syntheticData.index[0]} to {syntheticData.index[-1]}")

print("\nEngineering features...")
targetColumns = ["CSUSHPISA", "GDP", "UNRATE"]
engineeredData = pipeline.featureEngineer.engineerAllFeatures(
    syntheticData, targetColumns
)

print(f"Engineered data shape: {engineeredData.shape}")

print("\nPreparing train/validation/test splits...")
targetColumn = "CSUSHPISA"
splits = pipeline.prepareTrainTestSplits(engineeredData, targetColumn)

print(f"Train set: {splits['trainX'].shape}")
print(f"Validation set: {splits['valX'].shape}")
print(f"Test set: {splits['testX'].shape}")

print("\n" + "=" * 70)
print("Training Gradient Boosting Ensemble (XGBoost + CatBoost)")
print("=" * 70)

gbEnsemble = pipeline.trainGradientBoosting(splits)

print("\nEvaluating ensemble on test set...")
testMetrics = gbEnsemble.evaluate(splits["testX"], splits["testY"])

print("\nTest Set Performance:")
for modelName, metrics in testMetrics.items():
    print(f"\n{modelName.upper()}:")
    for metricName, value in metrics.items():
        print(f"  {metricName}: {value:.4f}")

print("\n" + "=" * 70)
print("Running Crisis Detection and Policy Recommendations")
print("=" * 70)

models = {"gradientBoosting": gbEnsemble}
predictionPipeline = PredictionPipeline(
    models=models, configPath=configPath
)

forecastResult = predictionPipeline.runPrediction(
    testX=splits["testX"], historicalY=splits["trainY"].values, targetName=targetColumn
)

print("\n" + "=" * 70)
print("QUICK START COMPLETED SUCCESSFULLY!")
print("=" * 70)
print("\nNext Steps:")
print("1. Get a FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html")
print("2. Run with real data: python main.py --fred-api-key YOUR_KEY --mode full")
print("3. Explore advanced features: TimesFM, Chronos, STGNN, AutoGluon")
print("4. Train on your own housing market data")
print("\nFor more information, see the documentation and examples.")
