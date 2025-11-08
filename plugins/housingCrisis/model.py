import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.modelRegistry.baseModel import (
    BaseModel, ModelMetadata, PredictionInput, PredictionOutput
)
from typing import Dict, Any
import time
import numpy as np
import pandas as pd
from datetime import datetime
import xgboost as xgb
from catboost import CatBoostRegressor
import torch
from sklearn.metrics import mean_squared_error

class HousingCrisisModel(BaseModel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.xgbModel = None
        self.catboostModel = None
        self.blendWeights = {"xgboost": 0.5, "catboost": 0.5}
        self.useGpu = torch.cuda.is_available()

    def getMetadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="housingCrisis",
            version="1.0.0",
            description="Multi-model ensemble for housing market crisis prediction using XGBoost and CatBoost",
            author="CloudEasyML",
            tags=["housing", "forecasting", "ensemble", "timeseries"],
            requirements=[
                "xgboost>=2.0.0",
                "catboost>=1.2.0",
                "torch>=2.0.0",
                "pandas>=2.0.0",
                "numpy>=1.24.0"
            ],
            gpuRequired=False,
            minMemoryGb=8,
            estimatedCostPerRequest=0.002
        )

    def load(self) -> None:
        xgbConfig = self.config.get('xgboost', {})
        catboostConfig = self.config.get('catboost', {})

        treeMethod = "gpu_hist" if self.useGpu else "hist"
        taskType = "GPU" if self.useGpu else "CPU"

        xgbParams = {
            "n_estimators": xgbConfig.get('nEstimators', 1000),
            "learning_rate": xgbConfig.get('learningRate', 0.05),
            "max_depth": xgbConfig.get('maxDepth', 7),
            "subsample": xgbConfig.get('subsample', 0.8),
            "colsample_bytree": xgbConfig.get('colsampleBytree', 0.8),
            "random_state": 42,
            "objective": "reg:squarederror",
            "tree_method": treeMethod,
        }

        catboostParams = {
            "iterations": catboostConfig.get('iterations', 1000),
            "learning_rate": catboostConfig.get('learningRate', 0.05),
            "depth": catboostConfig.get('depth', 7),
            "l2_leaf_reg": catboostConfig.get('l2LeafReg', 3.0),
            "random_state": 42,
            "task_type": taskType,
            "loss_function": "RMSE",
            "verbose": False,
        }

        self.xgbModel = xgb.XGBRegressor(**xgbParams)
        self.catboostModel = CatBoostRegressor(**catboostParams)
        self.isLoaded = True

    def predict(self, input: PredictionInput) -> PredictionOutput:
        if not self.isLoaded:
            raise RuntimeError("Model not loaded")

        startTime = time.time()

        df = pd.DataFrame(input.data) if isinstance(input.data, list) else input.data

        xgbPred = self.xgbModel.predict(df)
        catPred = self.catboostModel.predict(df)

        blended = (
            self.blendWeights["xgboost"] * xgbPred +
            self.blendWeights["catboost"] * catPred
        )

        crisisDetection = input.options.get('crisisDetection', False)
        metadata = {
            'modelVersions': {
                'xgboost': 'trained',
                'catboost': 'trained'
            },
            'blendWeights': self.blendWeights
        }

        if crisisDetection:
            crisisAnalysis = self._analyzeCrisis(blended, df)
            metadata.update(crisisAnalysis)

        processingTime = (time.time() - startTime) * 1000

        return PredictionOutput(
            predictions=blended.tolist(),
            metadata=metadata,
            processingTimeMs=processingTime
        )

    def train(self, trainingData: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.isLoaded:
            self.load()

        X = trainingData['X']
        y = trainingData['y']
        valX = trainingData.get('valX')
        valY = trainingData.get('valY')

        device = torch.cuda.get_device_name(0) if self.useGpu else "CPU"
        results = {'device': device}

        evalSetXgb = [(valX, valY)] if valX is not None else None
        evalSetCat = (valX, valY) if valX is not None else None

        if evalSetXgb:
            self.xgbModel.set_params(
                early_stopping_rounds=50,
                callbacks=[xgb.callback.EarlyStopping(rounds=50)]
            )

        self.xgbModel.fit(X, y, eval_set=evalSetXgb, verbose=False)
        results['xgboost'] = {
            'bestIteration': getattr(self.xgbModel, 'best_iteration',
                                    self.xgbModel.n_estimators)
        }

        fitParams = {'X': X, 'y': y}
        if evalSetCat:
            fitParams['eval_set'] = evalSetCat
            fitParams['early_stopping_rounds'] = 50
            fitParams['use_best_model'] = True

        self.catboostModel.fit(**fitParams)
        results['catboost'] = {
            'bestIteration': getattr(self.catboostModel, 'best_iteration_',
                                    self.catboostModel.get_params()['iterations'])
        }

        if valX is not None and valY is not None:
            self._optimizeBlendWeights(valX, valY)
            results['blendWeights'] = self.blendWeights

        return results

    def _optimizeBlendWeights(self, X: pd.DataFrame, y: pd.Series):
        xgbPred = self.xgbModel.predict(X)
        catPred = self.catboostModel.predict(X)

        bestRmse = float("inf")
        bestWeight = 0.5

        for weight in np.arange(0, 1.1, 0.1):
            blendedPred = weight * xgbPred + (1 - weight) * catPred
            rmse = np.sqrt(mean_squared_error(y, blendedPred))

            if rmse < bestRmse:
                bestRmse = rmse
                bestWeight = weight

        self.blendWeights = {"xgboost": bestWeight, "catboost": 1 - bestWeight}

    def _analyzeCrisis(self, predictions: np.ndarray,
                       features: pd.DataFrame) -> Dict[str, Any]:
        recentTrend = np.mean(np.diff(predictions[-12:])) if len(predictions) >= 12 else 0
        volatility = np.std(predictions) if len(predictions) > 1 else 0

        if recentTrend < -5 and volatility > 10:
            crisisLevel = "HIGH"
            crisisScore = 0.8
            recommendations = [
                "Immediate policy intervention recommended",
                "Monitor housing affordability metrics",
                "Consider mortgage rate stabilization"
            ]
        elif recentTrend < -2 or volatility > 5:
            crisisLevel = "MEDIUM"
            crisisScore = 0.5
            recommendations = [
                "Increase market monitoring frequency",
                "Prepare contingency plans",
                "Review lending standards"
            ]
        else:
            crisisLevel = "LOW"
            crisisScore = 0.2
            recommendations = [
                "Continue routine market monitoring",
                "Refine predictive models with latest data"
            ]

        return {
            'crisisLevel': crisisLevel,
            'crisisScore': crisisScore,
            'recommendations': recommendations,
            'metrics': {
                'recentTrend': float(recentTrend),
                'volatility': float(volatility)
            }
        }
