import xgboost as xgb
from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Optional, Dict, Tuple


class XGBoostForecaster:
    def __init__(
        self,
        nEstimators: int = 1000,
        learningRate: float = 0.05,
        maxDepth: int = 7,
        subsample: float = 0.8,
        colsampleBytree: float = 0.8,
        randomState: int = 42,
    ):
        self.useGpu = torch.cuda.is_available()
        treeMethod = "gpu_hist" if self.useGpu else "hist"

        self.params = {
            "n_estimators": nEstimators,
            "learning_rate": learningRate,
            "max_depth": maxDepth,
            "subsample": subsample,
            "colsample_bytree": colsampleBytree,
            "random_state": randomState,
            "objective": "reg:squarederror",
            "tree_method": treeMethod,
        }
        self.model = None
        self.featureImportance = None
        self.earlyStoppingRounds = 50

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        evalSet: Optional[list] = None,
        verbose: bool = True,
    ) -> Dict:
        modelParams = self.params.copy()

        if evalSet is not None:
            modelParams["early_stopping_rounds"] = self.earlyStoppingRounds
            modelParams["callbacks"] = [xgb.callback.EarlyStopping(rounds=self.earlyStoppingRounds)]

        self.model = xgb.XGBRegressor(**modelParams)

        fitParams = {"X": X, "y": y}
        if evalSet is not None:
            fitParams["eval_set"] = evalSet
        if verbose:
            fitParams["verbose"] = True

        self.model.fit(**fitParams)

        self.featureImportance = pd.DataFrame(
            {"feature": X.columns, "importance": self.model.feature_importances_}
        ).sort_values("importance", ascending=False)

        bestIteration = getattr(self.model, "best_iteration", self.params["n_estimators"])
        bestScore = getattr(self.model, "best_score", None)

        return {
            "bestIteration": bestIteration,
            "bestScore": bestScore,
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(X)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        predictions = self.predict(X)
        return {
            "rmse": np.sqrt(mean_squared_error(y, predictions)),
            "mae": mean_absolute_error(y, predictions),
            "r2": r2_score(y, predictions),
        }

    def getFeatureImportance(self) -> pd.DataFrame:
        return self.featureImportance

    def saveModel(self, path: str):
        if self.model:
            self.model.save_model(path)

    def loadModel(self, path: str):
        self.model = xgb.XGBRegressor()
        self.model.load_model(path)


class CatBoostForecaster:
    def __init__(
        self,
        iterations: int = 1000,
        learningRate: float = 0.05,
        depth: int = 7,
        l2LeafReg: float = 3.0,
        randomState: int = 42,
        taskType: Optional[str] = None,
    ):
        self.useGpu = torch.cuda.is_available()
        if taskType is None:
            taskType = "GPU" if self.useGpu else "CPU"

        self.params = {
            "iterations": iterations,
            "learning_rate": learningRate,
            "depth": depth,
            "l2_leaf_reg": l2LeafReg,
            "random_state": randomState,
            "task_type": taskType,
            "loss_function": "RMSE",
            "verbose": False,
        }
        self.model = None
        self.featureImportance = None
        self.earlyStoppingRounds = 50

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        evalSet: Optional[Tuple] = None,
        verbose: bool = True,
    ) -> Dict:
        self.model = CatBoostRegressor(**self.params)

        if verbose:
            self.model.set_params(verbose=100)

        fitParams = {"X": X, "y": y}

        if evalSet is not None:
            fitParams["eval_set"] = evalSet
            fitParams["early_stopping_rounds"] = self.earlyStoppingRounds
            fitParams["use_best_model"] = True

        self.model.fit(**fitParams)

        self.featureImportance = pd.DataFrame(
            {"feature": X.columns, "importance": self.model.feature_importances_}
        ).sort_values("importance", ascending=False)

        bestIteration = getattr(self.model, "best_iteration_", self.params["iterations"])
        bestScore = getattr(self.model, "best_score_", None)

        return {
            "bestIteration": bestIteration,
            "bestScore": bestScore,
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(X)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        predictions = self.predict(X)
        return {
            "rmse": np.sqrt(mean_squared_error(y, predictions)),
            "mae": mean_absolute_error(y, predictions),
            "r2": r2_score(y, predictions),
        }

    def getFeatureImportance(self) -> pd.DataFrame:
        return self.featureImportance

    def saveModel(self, path: str):
        if self.model:
            self.model.save_model(path)

    def loadModel(self, path: str):
        self.model = CatBoostRegressor()
        self.model.load_model(path)


class GradientBoostingEnsemble:
    def __init__(self, xgbConfig: Dict, catboostConfig: Dict):
        self.xgbForecaster = XGBoostForecaster(**xgbConfig)
        self.catboostForecaster = CatBoostForecaster(**catboostConfig)
        self.blendWeights = {"xgboost": 0.5, "catboost": 0.5}

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        valX: Optional[pd.DataFrame] = None,
        valY: Optional[pd.Series] = None,
    ) -> Dict:
        evalSetXgb = [(valX, valY)] if valX is not None and valY is not None else None
        evalSetCat = (valX, valY) if valX is not None and valY is not None else None

        device = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        print(f"Training on: {device}")

        print("Training XGBoost...")
        xgbResults = self.xgbForecaster.train(X, y, evalSet=evalSetXgb)

        print("Training CatBoost...")
        catboostResults = self.catboostForecaster.train(X, y, evalSet=evalSetCat)

        if valX is not None and valY is not None:
            self._optimizeBlendWeights(valX, valY)

        return {
            "xgboost": xgbResults,
            "catboost": catboostResults,
            "blendWeights": self.blendWeights,
        }

    def _optimizeBlendWeights(self, X: pd.DataFrame, y: pd.Series):
        xgbPred = self.xgbForecaster.predict(X)
        catPred = self.catboostForecaster.predict(X)

        bestRmse = float("inf")
        bestWeight = 0.5

        for weight in np.arange(0, 1.1, 0.1):
            blendedPred = weight * xgbPred + (1 - weight) * catPred
            rmse = np.sqrt(mean_squared_error(y, blendedPred))

            if rmse < bestRmse:
                bestRmse = rmse
                bestWeight = weight

        self.blendWeights = {"xgboost": bestWeight, "catboost": 1 - bestWeight}
        print(f"Optimized blend weights: {self.blendWeights}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        xgbPred = self.xgbForecaster.predict(X)
        catPred = self.catboostForecaster.predict(X)

        blended = (
            self.blendWeights["xgboost"] * xgbPred
            + self.blendWeights["catboost"] * catPred
        )

        return blended

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        predictions = self.predict(X)

        xgbMetrics = self.xgbForecaster.evaluate(X, y)
        catboostMetrics = self.catboostForecaster.evaluate(X, y)

        return {
            "ensemble": {
                "rmse": np.sqrt(mean_squared_error(y, predictions)),
                "mae": mean_absolute_error(y, predictions),
                "r2": r2_score(y, predictions),
            },
            "xgboost": xgbMetrics,
            "catboost": catboostMetrics,
        }
