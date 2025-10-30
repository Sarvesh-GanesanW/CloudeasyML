import torch
import numpy as np
from typing import List, Optional
import sys


class ChronosForecaster:
    def __init__(
        self,
        modelName: str = "amazon/chronos-bolt-small",
        deviceMap: str = "cuda",
        torchDtype: str = "bfloat16",
        predictionLength: int = 12,
        numSamples: int = 20,
    ):
        self.modelName = modelName
        self.deviceMap = deviceMap if torch.cuda.is_available() else "cpu"
        self.torchDtype = getattr(torch, torchDtype)
        self.predictionLength = predictionLength
        self.numSamples = numSamples
        self.pipeline = None

    def loadModel(self):
        try:
            from chronos import ChronosPipeline

            self.pipeline = ChronosPipeline.from_pretrained(
                self.modelName,
                device_map=self.deviceMap,
                torch_dtype=self.torchDtype,
            )
            print(f"Chronos model loaded successfully on {self.deviceMap}")
        except ImportError:
            print(
                "Chronos not installed. Install with: pip install git+https://github.com/amazon-science/chronos-forecasting.git"
            )
            sys.exit(1)
        except Exception as e:
            print(f"Error loading Chronos model: {e}")

    def predict(
        self,
        context: torch.Tensor,
        predictionLength: Optional[int] = None,
        numSamples: Optional[int] = None,
        temperature: float = 1.0,
        topK: int = 50,
        topP: float = 1.0,
    ) -> torch.Tensor:
        if self.pipeline is None:
            self.loadModel()

        predLen = predictionLength if predictionLength else self.predictionLength
        nSamples = numSamples if numSamples else self.numSamples

        try:
            forecast = self.pipeline.predict(
                context,
                predLen,
                num_samples=nSamples,
                temperature=temperature,
                top_k=topK,
                top_p=topP,
            )
            return forecast
        except Exception as e:
            print(f"Error during prediction: {e}")
            return None

    def predictFromArray(
        self, data: np.ndarray, predictionLength: Optional[int] = None
    ) -> np.ndarray:
        context = torch.tensor(data, dtype=torch.float32)

        if len(context.shape) == 1:
            context = context.unsqueeze(0)

        forecast = self.predict(context, predictionLength)

        if forecast is not None:
            return forecast.numpy().mean(axis=1)
        return np.array([])

    def predictBatch(
        self, dataList: List[np.ndarray], predictionLength: Optional[int] = None
    ) -> List[np.ndarray]:
        results = []
        for data in dataList:
            prediction = self.predictFromArray(data, predictionLength)
            results.append(prediction)
        return results

    def predictWithUncertainty(
        self,
        data: np.ndarray,
        predictionLength: Optional[int] = None,
        confidenceLevel: float = 0.95,
    ) -> dict:
        context = torch.tensor(data, dtype=torch.float32)
        if len(context.shape) == 1:
            context = context.unsqueeze(0)

        forecast = self.predict(context, predictionLength)

        if forecast is not None:
            forecastNumpy = forecast.numpy()

            mean = forecastNumpy.mean(axis=1).squeeze()
            median = np.median(forecastNumpy, axis=1).squeeze()
            std = forecastNumpy.std(axis=1).squeeze()

            alpha = 1 - confidenceLevel
            lowerQuantile = alpha / 2
            upperQuantile = 1 - lowerQuantile

            lower = np.quantile(forecastNumpy, lowerQuantile, axis=1).squeeze()
            upper = np.quantile(forecastNumpy, upperQuantile, axis=1).squeeze()

            return {
                "mean": mean,
                "median": median,
                "std": std,
                "lower": lower,
                "upper": upper,
                "confidenceLevel": confidenceLevel,
            }
        return {}

    def getModelInfo(self):
        return {
            "modelName": self.modelName,
            "deviceMap": self.deviceMap,
            "predictionLength": self.predictionLength,
            "numSamples": self.numSamples,
        }
