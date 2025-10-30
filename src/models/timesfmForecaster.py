import torch
import numpy as np
from typing import List, Tuple, Optional
import sys


class TimesFMForecaster:
    def __init__(
        self,
        modelName: str = "google/timesfm-2.5-200m-pytorch",
        maxContext: int = 1024,
        maxHorizon: int = 256,
        normalizeInputs: bool = True,
        device: str = "cuda",
    ):
        self.modelName = modelName
        self.maxContext = maxContext
        self.maxHorizon = maxHorizon
        self.normalizeInputs = normalizeInputs
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = None
        self.isCompiled = False

    def loadModel(self):
        try:
            import timesfm

            torch.set_float32_matmul_precision("high")
            self.model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(self.modelName)
            print(f"TimesFM model loaded successfully on {self.device}")
        except ImportError:
            print(
                "TimesFM not installed. Install with: pip install git+https://github.com/google-research/timesfm.git"
            )
            sys.exit(1)

    def compileModel(self):
        if self.model is None:
            self.loadModel()

        try:
            import timesfm

            self.model.compile(
                timesfm.ForecastConfig(
                    max_context=self.maxContext,
                    max_horizon=self.maxHorizon,
                    normalize_inputs=self.normalizeInputs,
                    use_continuous_quantile_head=True,
                    force_flip_invariance=True,
                    infer_is_positive=True,
                    fix_quantile_crossing=True,
                )
            )
            self.isCompiled = True
            print("TimesFM model compiled successfully")
        except Exception as e:
            print(f"Error compiling model: {e}")

    def forecast(
        self, inputs: List[np.ndarray], horizon: int = 12
    ) -> Tuple[np.ndarray, np.ndarray]:
        if not self.isCompiled:
            self.compileModel()

        try:
            pointForecast, quantileForecast = self.model.forecast(
                horizon=horizon,
                inputs=inputs,
            )
            return pointForecast, quantileForecast
        except Exception as e:
            print(f"Error during forecasting: {e}")
            return None, None

    def predictSingleSeries(self, series: np.ndarray, horizon: int = 12) -> np.ndarray:
        if len(series.shape) == 1:
            series = [series]

        pointForecast, _ = self.forecast(series, horizon)

        if pointForecast is not None:
            return pointForecast[0] if len(pointForecast) > 0 else np.array([])
        return np.array([])

    def predictBatch(
        self, seriesList: List[np.ndarray], horizon: int = 12
    ) -> List[np.ndarray]:
        pointForecast, _ = self.forecast(seriesList, horizon)

        if pointForecast is not None:
            return [pointForecast[i] for i in range(len(pointForecast))]
        return []

    def getModelInfo(self):
        return {
            "modelName": self.modelName,
            "maxContext": self.maxContext,
            "maxHorizon": self.maxHorizon,
            "normalizeInputs": self.normalizeInputs,
            "device": self.device,
            "isCompiled": self.isCompiled,
        }
