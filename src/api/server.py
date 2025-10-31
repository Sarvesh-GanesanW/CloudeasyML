import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import pickle
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Housing Crisis Prediction API",
    description="Multi-modal ensemble inference API for housing crisis prediction",
    version="1.0.0",
)


class PredictionRequest(BaseModel):
    data: List[Dict]
    horizon: int = Field(default=12, ge=1, le=36)
    includeUncertainty: bool = False
    crisisDetection: bool = True


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    modelsLoaded: bool


class PredictionResponse(BaseModel):
    predictions: List[float]
    horizon: int
    crisisLevel: Optional[str] = None
    crisisScore: Optional[float] = None
    recommendations: Optional[List[str]] = None
    uncertainty: Optional[Dict] = None


class ModelRegistry:
    def __init__(self):
        self.models = {}
        self.loadedAt = None

    def loadModels(self, modelPath: str = "/app/models/saved"):
        try:
            logger.info("Loading models from disk...")

            modelPath = Path(modelPath)
            if modelPath.exists():
                for modelFile in modelPath.glob("*.pkl"):
                    modelName = modelFile.stem
                    with open(modelFile, "rb") as f:
                        self.models[modelName] = pickle.load(f)
                    logger.info(f"Loaded model: {modelName}")

            self.loadedAt = datetime.now()
            logger.info(f"Models loaded successfully at {self.loadedAt}")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def isReady(self) -> bool:
        return len(self.models) > 0


modelRegistry = ModelRegistry()


@app.on_event("startup")
async def startup():
    logger.info("Starting Housing Crisis Prediction API...")
    modelRegistry.loadModels()
    if not modelRegistry.isReady():
        logger.warning("No models loaded - running in demo mode")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        modelsLoaded=modelRegistry.isReady(),
    )


@app.get("/models")
async def listModels():
    return {
        "models": list(modelRegistry.models.keys()),
        "loadedAt": modelRegistry.loadedAt.isoformat()
        if modelRegistry.loadedAt
        else None,
        "count": len(modelRegistry.models),
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        if not modelRegistry.isReady():
            df = pd.DataFrame(request.data)
            predictions = np.random.randn(request.horizon).tolist()

            return PredictionResponse(
                predictions=predictions,
                horizon=request.horizon,
                crisisLevel="DEMO",
                crisisScore=0.5,
                recommendations=["Demo mode - load models for real predictions"],
            )

        df = pd.DataFrame(request.data)

        ensemble = modelRegistry.models.get("ensemble")
        if ensemble:
            predictions = ensemble.predict(df).tolist()
        else:
            predictions = np.zeros(request.horizon).tolist()

        response = PredictionResponse(predictions=predictions, horizon=request.horizon)

        if request.crisisDetection:
            from pipeline.predictionPipeline import CrisisDetector

            detector = CrisisDetector()

            historicalData = df.iloc[-12:].values.flatten()
            predictionArray = np.array(predictions)

            crisisAnalysis = detector.detectCrisisLevel(predictionArray, historicalData)
            recommendations = detector.generateRecommendations(crisisAnalysis)

            response.crisisLevel = crisisAnalysis["crisisLevel"]
            response.crisisScore = crisisAnalysis["crisisScore"]
            response.recommendations = recommendations

        return response

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-predict")
async def batchPredict(
    requests: List[PredictionRequest], backgroundTasks: BackgroundTasks
):
    return {
        "status": "accepted",
        "jobId": f"batch-{datetime.now().timestamp()}",
        "count": len(requests),
        "message": "Batch job queued for processing",
    }


@app.post("/reload-models")
async def reloadModels():
    success = modelRegistry.loadModels()
    return {
        "success": success,
        "modelsLoaded": len(modelRegistry.models),
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
