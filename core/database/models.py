from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class User(BaseModel):
    userId: str
    email: str
    name: str
    createdAt: datetime = Field(default_factory=datetime.now)
    tier: str = "free"
    isActive: bool = True
    metadata: Dict[str, Any] = {}

class Deployment(BaseModel):
    deploymentId: str
    userId: str
    modelName: str
    modelVersion: str
    status: str
    createdAt: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any] = {}
    endpoint: Optional[str] = None
    resources: Dict[str, Any] = {}

class UsageRecord(BaseModel):
    recordId: str
    userId: str
    deploymentId: str
    modelName: str
    timestamp: datetime = Field(default_factory=datetime.now)
    requestCount: int = 1
    processingTimeMs: float
    cost: float = 0.0
    metadata: Dict[str, Any] = {}
