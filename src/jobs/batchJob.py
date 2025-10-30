import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import argparse
import json
import logging
from datetime import datetime
import boto3
from typing import Dict, Optional

from pipeline.trainingPipeline import TrainingPipeline
from pipeline.predictionPipeline import PredictionPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BatchJobRunner:
    def __init__(self, jobConfig: Dict):
        self.jobConfig = jobConfig
        self.jobId = f"job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.s3Client = None

        if jobConfig.get("useS3", False):
            self.s3Client = boto3.client("s3")

    def runTrainingJob(self) -> Dict:
        logger.info(f"Starting training job: {self.jobId}")

        pipeline = TrainingPipeline(configPath=self.jobConfig.get("configPath"))

        results = pipeline.runFullPipeline(
            fredApiKey=self.jobConfig.get("fredApiKey"),
            targetColumn=self.jobConfig.get("targetColumn", "CSUSHPISA"),
            useAutoGluon=self.jobConfig.get("useAutoGluon", False),
        )

        if self.jobConfig.get("saveModels", True):
            self._saveModels(results["models"])

        logger.info(f"Training job completed: {self.jobId}")

        return {
            "jobId": self.jobId,
            "status": "completed",
            "targetColumn": results["targetColumn"],
            "modelsCount": len(results["models"]),
            "timestamp": datetime.now().isoformat(),
        }

    def runPredictionJob(self) -> Dict:
        logger.info(f"Starting prediction job: {self.jobId}")

        models = self._loadModels()

        predictionPipeline = PredictionPipeline(
            models=models, configPath=self.jobConfig.get("configPath")
        )

        inputData = self._loadInputData()

        results = predictionPipeline.runPrediction(
            testX=inputData["testX"],
            historicalY=inputData["historicalY"],
            targetName=self.jobConfig.get("targetColumn", "Housing Price Index"),
        )

        if self.jobConfig.get("saveResults", True):
            self._saveResults(results)

        logger.info(f"Prediction job completed: {self.jobId}")

        return {
            "jobId": self.jobId,
            "status": "completed",
            "predictions": len(results["predictions"]),
            "crisisLevel": results["crisisAnalysis"]["crisisLevel"],
            "timestamp": datetime.now().isoformat(),
        }

    def _saveModels(self, models: Dict):
        savePath = Path(self.jobConfig.get("modelOutputPath", "/app/models/saved"))
        savePath.mkdir(parents=True, exist_ok=True)

        import pickle

        for modelName, model in models.items():
            modelFile = savePath / f"{modelName}_{self.jobId}.pkl"
            with open(modelFile, "wb") as f:
                pickle.dump(model, f)
            logger.info(f"Saved model: {modelFile}")

            if self.s3Client and self.jobConfig.get("s3Bucket"):
                s3Key = f"models/{modelName}_{self.jobId}.pkl"
                self.s3Client.upload_file(
                    str(modelFile), self.jobConfig["s3Bucket"], s3Key
                )
                logger.info(
                    f"Uploaded to S3: s3://{self.jobConfig['s3Bucket']}/{s3Key}"
                )

    def _loadModels(self) -> Dict:
        import pickle

        models = {}

        if self.s3Client and self.jobConfig.get("s3Bucket"):
            s3Prefix = self.jobConfig.get("s3ModelPrefix", "models/")
            response = self.s3Client.list_objects_v2(
                Bucket=self.jobConfig["s3Bucket"], Prefix=s3Prefix
            )

            for obj in response.get("Contents", []):
                if obj["Key"].endswith(".pkl"):
                    tmpFile = Path(f"/tmp/{Path(obj['Key']).name}")
                    self.s3Client.download_file(
                        self.jobConfig["s3Bucket"], obj["Key"], str(tmpFile)
                    )

                    with open(tmpFile, "rb") as f:
                        modelName = tmpFile.stem.split("_")[0]
                        models[modelName] = pickle.load(f)
                    logger.info(f"Loaded model from S3: {obj['Key']}")
        else:
            modelPath = Path(self.jobConfig.get("modelInputPath", "/app/models/saved"))
            for modelFile in modelPath.glob("*.pkl"):
                with open(modelFile, "rb") as f:
                    models[modelFile.stem] = pickle.load(f)
                logger.info(f"Loaded model: {modelFile}")

        return models

    def _loadInputData(self) -> Dict:
        import pandas as pd

        if self.s3Client and self.jobConfig.get("s3InputPath"):
            tmpFile = Path("/tmp/input_data.parquet")
            self.s3Client.download_file(
                self.jobConfig["s3Bucket"], self.jobConfig["s3InputPath"], str(tmpFile)
            )
            df = pd.read_parquet(tmpFile)
        else:
            inputPath = Path(
                self.jobConfig.get("inputDataPath", "data/processed/input.parquet")
            )
            df = pd.read_parquet(inputPath)

        return {
            "testX": df.drop("target", axis=1) if "target" in df.columns else df,
            "historicalY": df["target"].values
            if "target" in df.columns
            else df.iloc[:, 0].values,
        }

    def _saveResults(self, results: Dict):
        import pandas as pd

        outputPath = Path(self.jobConfig.get("outputPath", "/app/output"))
        outputPath.mkdir(parents=True, exist_ok=True)

        resultsFile = outputPath / f"results_{self.jobId}.json"
        with open(resultsFile, "w") as f:
            json.dump(
                {
                    "predictions": results["predictions"].tolist()
                    if hasattr(results["predictions"], "tolist")
                    else results["predictions"],
                    "crisisAnalysis": results["crisisAnalysis"],
                    "recommendations": results["recommendations"],
                },
                f,
                indent=2,
            )
        logger.info(f"Saved results: {resultsFile}")

        if self.s3Client and self.jobConfig.get("s3Bucket"):
            s3Key = f"results/results_{self.jobId}.json"
            self.s3Client.upload_file(
                str(resultsFile), self.jobConfig["s3Bucket"], s3Key
            )
            logger.info(f"Uploaded to S3: s3://{self.jobConfig['s3Bucket']}/{s3Key}")


def main():
    parser = argparse.ArgumentParser(description="Housing Crisis Batch Job Runner")
    parser.add_argument(
        "--job-type",
        required=True,
        choices=["train", "predict"],
        help="Type of job to run",
    )
    parser.add_argument(
        "--config-file", type=str, default=None, help="Job configuration file (JSON)"
    )
    parser.add_argument("--fred-api-key", type=str, default=None, help="FRED API key")
    parser.add_argument(
        "--s3-bucket", type=str, default=None, help="S3 bucket for input/output"
    )
    parser.add_argument(
        "--target-column",
        type=str,
        default="CSUSHPISA",
        help="Target column for prediction",
    )

    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, "r") as f:
            jobConfig = json.load(f)
    else:
        jobConfig = {
            "fredApiKey": args.fred_api_key,
            "s3Bucket": args.s3_bucket,
            "targetColumn": args.target_column,
            "useS3": args.s3_bucket is not None,
        }

    runner = BatchJobRunner(jobConfig)

    try:
        if args.job_type == "train":
            result = runner.runTrainingJob()
        else:
            result = runner.runPredictionJob()

        print(json.dumps(result, indent=2))
        return 0

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
