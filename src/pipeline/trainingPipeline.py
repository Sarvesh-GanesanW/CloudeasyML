import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from models.timesfmForecaster import TimesFMForecaster
from models.chronosForecaster import ChronosForecaster
from models.stgnnModel import STGNNForecaster
from models.gradientBoostingModels import GradientBoostingEnsemble
from ensemble.stackedEnsemble import StackedEnsemble, AutoGluonEnsemble
from data.dataCollector import DataCollector
from data.featureEngineer import FeatureEngineer
from utils.configLoader import ConfigLoader
from typing import Dict, Tuple, Optional


class TrainingPipeline:
    def __init__(self, configPath: str = "config/config.yaml"):
        self.config = ConfigLoader(configPath)
        self.dataCollector = None
        self.featureEngineer = FeatureEngineer()

        self.models = {}
        self.trainedData = {}

    def initializeDataCollector(self, fredApiKey: Optional[str] = None):
        dataConfig = self.config.getDataConfig()
        self.dataCollector = DataCollector(
            fredApiKey=fredApiKey, cachePath=dataConfig.get("rawDataPath", "data/raw")
        )

    def collectAndPrepareData(self) -> pd.DataFrame:
        print("Collecting data from FRED and Zillow...")
        allData = self.dataCollector.collectAllData()

        economicDf = allData["economic"]
        housingDf = allData["housing"]

        combinedDf = pd.concat([economicDf, housingDf], axis=1)
        combinedDf = combinedDf.dropna()

        print(f"Raw data shape: {combinedDf.shape}")

        print("Engineering features...")
        targetColumns = [
            col
            for col in combinedDf.columns
            if col in ["CSUSHPISA", "MSPUS", "USSTHPI"]
        ]

        if not targetColumns:
            targetColumns = [combinedDf.columns[0]]

        engineeredDf = self.featureEngineer.engineerAllFeatures(
            combinedDf, targetColumns
        )

        print(f"Engineered data shape: {engineeredDf.shape}")

        return engineeredDf

    def prepareTrainTestSplits(self, data: pd.DataFrame, targetColumn: str) -> Dict:
        trainingConfig = self.config.getTrainingConfig()

        trainRatio = 1 - trainingConfig["validationSplit"] - trainingConfig["testSplit"]
        valRatio = trainingConfig["validationSplit"]

        trainX, trainY, valX, valY, testX, testY = (
            self.featureEngineer.splitTimeSeriesData(
                data, targetColumn, trainRatio, valRatio
            )
        )

        return {
            "trainX": trainX,
            "trainY": trainY,
            "valX": valX,
            "valY": valY,
            "testX": testX,
            "testY": testY,
        }

    def trainTimesFM(self, data: Dict) -> TimesFMForecaster:
        print("\nTraining TimesFM model...")
        timesfmConfig = self.config.getModelConfig("timesfm")

        forecaster = TimesFMForecaster(
            modelName=timesfmConfig["modelName"],
            maxContext=timesfmConfig["maxContext"],
            maxHorizon=timesfmConfig["maxHorizon"],
            normalizeInputs=timesfmConfig["normalizeInputs"],
        )

        forecaster.compileModel()

        print("TimesFM model ready for forecasting")
        return forecaster

    def trainChronos(self, data: Dict) -> ChronosForecaster:
        print("\nTraining Chronos model...")
        chronosConfig = self.config.getModelConfig("chronos")

        forecaster = ChronosForecaster(
            modelName=chronosConfig["modelName"],
            deviceMap=chronosConfig["deviceMap"],
            torchDtype=chronosConfig["torchDtype"],
            predictionLength=chronosConfig["predictionLength"],
        )

        forecaster.loadModel()

        print("Chronos model ready for forecasting")
        return forecaster

    def trainGradientBoosting(self, data: Dict) -> GradientBoostingEnsemble:
        print("\nTraining Gradient Boosting models...")
        xgbConfig = self.config.getModelConfig("xgboost")
        catboostConfig = self.config.getModelConfig("catboost")

        ensemble = GradientBoostingEnsemble(xgbConfig, catboostConfig)

        results = ensemble.train(
            data["trainX"], data["trainY"], data["valX"], data["valY"]
        )

        print(f"\nGradient Boosting results: {results}")

        valMetrics = ensemble.evaluate(data["valX"], data["valY"])
        print(f"Validation metrics: {valMetrics}")

        return ensemble

    def createStackedEnsemble(self, baseModels: Dict, data: Dict) -> StackedEnsemble:
        print("\nCreating stacked ensemble...")

        ensemble = StackedEnsemble(
            metaLearnerType="ridge", metaLearnerParams={"alpha": 1.0}
        )

        for name, model in baseModels.items():
            ensemble.addBaseModel(name, model)

        trainMetrics = ensemble.trainMetaLearner(data["trainX"], data["trainY"])
        print(f"Meta-learner training metrics: {trainMetrics}")

        valMetrics = ensemble.evaluate(data["valX"], data["valY"])
        print(f"Ensemble validation metrics: {valMetrics}")

        weights = ensemble.getModelWeights()
        print(f"Ensemble weights: {weights}")

        return ensemble

    def trainAutoGluonEnsemble(
        self, data: Dict, targetColumn: str
    ) -> AutoGluonEnsemble:
        print("\nTraining AutoGluon ensemble...")
        ensembleConfig = self.config.getEnsembleConfig()

        trainData = data["trainX"].copy()
        trainData[targetColumn] = data["trainY"]

        valData = data["valX"].copy()
        valData[targetColumn] = data["valY"]

        ensemble = AutoGluonEnsemble(
            timeLimit=ensembleConfig["timeLimit"],
            preset=ensembleConfig["preset"],
            evalMetric=ensembleConfig["evalMetric"],
        )

        leaderboard = ensemble.train(trainData, targetColumn, valData)

        if leaderboard is not None:
            print(f"\nLeaderboard:\n{leaderboard}")

        return ensemble

    def runFullPipeline(
        self,
        fredApiKey: Optional[str] = None,
        targetColumn: str = "CSUSHPISA",
        useAutoGluon: bool = True,
    ) -> Dict:
        self.initializeDataCollector(fredApiKey)

        data = self.collectAndPrepareData()

        if targetColumn not in data.columns:
            availableTargets = [
                col
                for col in data.columns
                if "price" in col.lower() or "hpi" in col.lower()
            ]
            if availableTargets:
                targetColumn = availableTargets[0]
            else:
                targetColumn = data.columns[-1]

        splits = self.prepareTrainTestSplits(data, targetColumn)

        gbEnsemble = self.trainGradientBoosting(splits)

        self.models["gradientBoosting"] = gbEnsemble
        self.trainedData = splits

        if useAutoGluon:
            autoGluonEnsemble = self.trainAutoGluonEnsemble(splits, targetColumn)
            self.models["autoGluon"] = autoGluonEnsemble

        print("\n" + "=" * 50)
        print("Training Pipeline Completed Successfully!")
        print("=" * 50)

        return {
            "models": self.models,
            "data": self.trainedData,
            "targetColumn": targetColumn,
        }
