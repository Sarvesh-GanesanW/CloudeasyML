from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel as PydanticBaseModel, Field
from datetime import datetime

class ModelMetadata(PydanticBaseModel):
    name: str
    version: str
    description: str
    author: str
    createdAt: datetime = Field(default_factory=datetime.now)
    tags: List[str] = []
    requirements: List[str] = []
    gpuRequired: bool = False
    minMemoryGb: int = 4
    estimatedCostPerRequest: float = 0.0

class PredictionInput(PydanticBaseModel):
    data: Any
    options: Optional[Dict[str, Any]] = {}

class PredictionOutput(PydanticBaseModel):
    predictions: Any
    metadata: Dict[str, Any] = {}
    processingTimeMs: float

class BaseModel(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.isLoaded = False

    @abstractmethod
    def getMetadata(self) -> ModelMetadata:
        pass

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def predict(self, input: PredictionInput) -> PredictionOutput:
        pass

    @abstractmethod
    def train(self, trainingData: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def unload(self) -> None:
        self.isLoaded = False

    def healthCheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self.isLoaded else "not_loaded",
            "metadata": self.getMetadata().dict()
        }
