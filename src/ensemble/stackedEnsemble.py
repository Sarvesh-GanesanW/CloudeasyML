import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import List, Dict, Optional
import pickle


class StackedEnsemble:
    def __init__(
        self, metaLearnerType: str = "ridge", metaLearnerParams: Optional[Dict] = None
    ):
        self.metaLearnerType = metaLearnerType
        self.metaLearnerParams = metaLearnerParams or {}
        self.metaLearner = self._initMetaLearner()
        self.baseModels = {}
        self.basePredictions = {}

    def _initMetaLearner(self):
        if self.metaLearnerType == "ridge":
            return Ridge(**self.metaLearnerParams)
        elif self.metaLearnerType == "lasso":
            return Lasso(**self.metaLearnerParams)
        elif self.metaLearnerType == "rf":
            return RandomForestRegressor(**self.metaLearnerParams)
        else:
            raise ValueError(f"Unknown meta learner type: {self.metaLearnerType}")

    def addBaseModel(self, name: str, model):
        self.baseModels[name] = model

    def generateBasePredictions(
        self, X: pd.DataFrame, stage: str = "train"
    ) -> np.ndarray:
        predictions = []

        for name, model in self.baseModels.items():
            if hasattr(model, "predict"):
                pred = model.predict(X)
                predictions.append(pred)
                print(f"Generated predictions from {name}")
            else:
                raise ValueError(f"Model {name} does not have a predict method")

        stackedPredictions = np.column_stack(predictions)
        self.basePredictions[stage] = stackedPredictions

        return stackedPredictions

    def trainMetaLearner(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        basePredictions = self.generateBasePredictions(X, stage="train")

        self.metaLearner.fit(basePredictions, y)

        metaPredictions = self.metaLearner.predict(basePredictions)

        metrics = {
            "rmse": np.sqrt(mean_squared_error(y, metaPredictions)),
            "mae": mean_absolute_error(y, metaPredictions),
            "r2": r2_score(y, metaPredictions),
        }

        if hasattr(self.metaLearner, "coef_"):
            self.ensembleWeights = self.metaLearner.coef_
            print(f"Meta-learner weights: {self.ensembleWeights}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        basePredictions = self.generateBasePredictions(X, stage="test")
        return self.metaLearner.predict(basePredictions)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        predictions = self.predict(X)

        metrics = {
            "ensemble": {
                "rmse": np.sqrt(mean_squared_error(y, predictions)),
                "mae": mean_absolute_error(y, predictions),
                "r2": r2_score(y, predictions),
            }
        }

        for name, model in self.baseModels.items():
            if hasattr(model, "predict"):
                basePred = model.predict(X)
                metrics[name] = {
                    "rmse": np.sqrt(mean_squared_error(y, basePred)),
                    "mae": mean_absolute_error(y, basePred),
                    "r2": r2_score(y, basePred),
                }

        return metrics

    def getModelWeights(self) -> Dict:
        if hasattr(self.metaLearner, "coef_"):
            modelNames = list(self.baseModels.keys())
            weights = self.metaLearner.coef_
            return dict(zip(modelNames, weights))
        return {}

    def saveEnsemble(self, path: str):
        ensembleData = {
            "metaLearner": self.metaLearner,
            "metaLearnerType": self.metaLearnerType,
            "baseModelNames": list(self.baseModels.keys()),
        }
        with open(path, "wb") as f:
            pickle.dump(ensembleData, f)

    def loadEnsemble(self, path: str):
        with open(path, "rb") as f:
            ensembleData = pickle.load(f)
        self.metaLearner = ensembleData["metaLearner"]
        self.metaLearnerType = ensembleData["metaLearnerType"]


class AutoGluonEnsemble:
    def __init__(
        self,
        timeLimit: int = 600,
        preset: str = "best_quality",
        evalMetric: str = "RMSE",
    ):
        self.timeLimit = timeLimit
        self.preset = preset
        self.evalMetric = evalMetric
        self.predictor = None

    def train(
        self,
        trainData: pd.DataFrame,
        targetColumn: str,
        validationData: Optional[pd.DataFrame] = None,
    ):
        try:
            from autogluon.tabular import TabularPredictor

            self.predictor = TabularPredictor(
                label=targetColumn,
                eval_metric=self.evalMetric,
                problem_type="regression",
            )

            self.predictor.fit(
                train_data=trainData,
                tuning_data=validationData,
                time_limit=self.timeLimit,
                presets=self.preset,
                verbosity=2,
            )

            print("AutoGluon training completed")

            leaderboard = self.predictor.leaderboard(trainData)
            return leaderboard

        except ImportError:
            print("AutoGluon not installed. Install with: pip install autogluon")
            return None

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.predictor is None:
            raise ValueError("Model not trained yet")
        return self.predictor.predict(X)

    def evaluate(self, testData: pd.DataFrame) -> Dict:
        if self.predictor is None:
            raise ValueError("Model not trained yet")

        performance = self.predictor.evaluate(testData)
        return performance

    def getFeatureImportance(self, data: pd.DataFrame) -> pd.DataFrame:
        if self.predictor is None:
            raise ValueError("Model not trained yet")
        return self.predictor.feature_importance(data)

    def saveModel(self, path: str):
        if self.predictor:
            self.predictor.save(path)

    def loadModel(self, path: str):
        from autogluon.tabular import TabularPredictor

        self.predictor = TabularPredictor.load(path)
