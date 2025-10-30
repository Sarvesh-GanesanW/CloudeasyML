import xgboost as xgb
from catboost import CatBoostRegressor
import numpy as np
import pandas as pd
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
        self.params = {
            "n_estimators": nEstimators,
            "learning_rate": learningRate,
            "max_depth": maxDepth,
            "subsample": subsample,
            "colsample_bytree": colsampleBytree,
            "random_state": randomState,
            "objective": "reg:squarederror",
            "tree_method": "gpu_hist"
            if xgb.get_config().get("use_gpu", False)
            else "hist",
        }
        self.model = None
        self.featureImportance = None

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        evalSet: Optional[list] = None,
        earlyStoppingRounds: int = 50,
        verbose: bool = True,
    ) -> Dict:
        self.model = xgb.XGBRegressor(**self.params)

        self.model.fit(
            X,
            y,
            eval_set=evalSet,
            early_stopping_rounds=earlyStoppingRounds,
            verbose=verbose,
        )

        self.featureImportance = pd.DataFrame(
            {"feature": X.columns, "importance": self.model.feature_importances_}
        ).sort_values("importance", ascending=False)

        return {
            "bestIteration": self.model.best_iteration,
            "bestScore": self.model.best_score,
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
        taskType: str = "GPU",
    ):
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

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        evalSet: Optional[Tuple] = None,
        earlyStoppingRounds: int = 50,
        verbose: bool = True,
    ) -> Dict:
        self.model = CatBoostRegressor(**self.params)

        if verbose:
            self.model.set_params(verbose=100)

        self.model.fit(
            X,
            y,
            eval_set=evalSet,
            early_stopping_rounds=earlyStoppingRounds,
            use_best_model=True,
        )

        self.featureImportance = pd.DataFrame(
            {"feature": X.columns, "importance": self.model.feature_importances_}
        ).sort_values("importance", ascending=False)

        return {
            "bestIteration": self.model.best_iteration_,
            "bestScore": self.model.best_score_,
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
