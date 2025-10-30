import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

import argparse
import warnings

warnings.filterwarnings("ignore")

from pipeline.trainingPipeline import TrainingPipeline
from pipeline.predictionPipeline import PredictionPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Housing Crisis Prediction Ensemble System"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="train",
        choices=["train", "predict", "full"],
        help="Mode: train, predict, or full pipeline",
    )
    parser.add_argument(
        "--fred-api-key",
        type=str,
        default=None,
        help="FRED API key for data collection",
    )
    parser.add_argument(
        "--target", type=str, default="CSUSHPISA", help="Target variable for prediction"
    )
    parser.add_argument(
        "--use-autogluon",
        action="store_true",
        help="Use AutoGluon for ensemble optimization",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file",
    )

    args = parser.parse_args()

    if args.mode in ["train", "full"]:
        print("=" * 70)
        print("HOUSING CRISIS PREDICTION SYSTEM - TRAINING MODE")
        print("=" * 70)

        pipeline = TrainingPipeline(configPath=args.config)

        results = pipeline.runFullPipeline(
            fredApiKey=args.fred_api_key,
            targetColumn=args.target,
            useAutoGluon=args.use_autogluon,
        )

        if args.mode == "full":
            print("\n" + "=" * 70)
            print("RUNNING PREDICTION PIPELINE")
            print("=" * 70)

            predictionPipeline = PredictionPipeline(
                models=results["models"], configPath=args.config
            )

            data = results["data"]
            forecastResult = predictionPipeline.runPrediction(
                testX=data["testX"],
                historicalY=data["trainY"].values,
                targetName=args.target,
            )

    elif args.mode == "predict":
        print("Prediction mode requires pre-trained models.")
        print("Please run in 'train' or 'full' mode first.")


if __name__ == "__main__":
    main()
