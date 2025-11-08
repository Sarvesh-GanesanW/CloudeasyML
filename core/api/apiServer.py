from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import uuid
from datetime import datetime

from core.modelRegistry.modelManager import ModelManager
from core.modelRegistry.baseModel import PredictionInput, PredictionOutput
from core.auth.apiKeyManager import ApiKeyManager, ApiKey
from core.auth.authMiddleware import AuthMiddleware
from core.database.databaseManager import DatabaseManager
from core.database.models import User, Deployment
from core.billing.usageTracker import UsageTracker
from core.billing.pricingEngine import PricingEngine

class CreateDeploymentRequest(BaseModel):
    modelName: str
    modelVersion: str = "latest"
    config: Dict[str, Any] = {}

class PredictRequest(BaseModel):
    deploymentId: str
    data: Any
    options: Optional[Dict[str, Any]] = {}

class CreateApiKeyRequest(BaseModel):
    name: str
    expiresInDays: Optional[int] = None
    rateLimit: int = 1000

class ApiServer:
    def __init__(self, pluginsPath: str = "plugins", dbPath: str = "data/db"):
        self.app = FastAPI(
            title="CloudEasyML",
            description="Plug-and-play ML model deployment platform",
            version="1.0.0"
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.db = DatabaseManager(dbPath)
        self.modelManager = ModelManager(pluginsPath)
        self.modelManager.loadAllPlugins()
        self.apiKeyManager = ApiKeyManager(self.db)
        self.authMiddleware = AuthMiddleware(self.apiKeyManager)
        self.pricingEngine = PricingEngine()
        self.usageTracker = UsageTracker(self.db, self.pricingEngine)

        self.security = HTTPBearer()
        self._setupRoutes()

    def _setupRoutes(self) -> None:
        @self.app.get("/health")
        async def healthCheck():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "modelsLoaded": len(self.modelManager.registeredModels)
            }

        @self.app.get("/models")
        async def listModels():
            return {
                "models": [m.dict() for m in self.modelManager.listModels()]
            }

        @self.app.post("/deployments")
        async def createDeployment(
            request: CreateDeploymentRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)

            deployment = Deployment(
                deploymentId=str(uuid.uuid4()),
                userId=apiKey.userId,
                modelName=request.modelName,
                modelVersion=request.modelVersion,
                status="active",
                config=request.config,
                endpoint=f"/predict/{request.modelName}"
            )

            self.db.saveDeployment(deployment)

            return {
                "deployment": deployment.dict(),
                "message": "Deployment created successfully"
            }

        @self.app.get("/deployments")
        async def listDeployments(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)
            deployments = self.db.getUserDeployments(apiKey.userId)

            return {
                "deployments": [d.dict() for d in deployments]
            }

        @self.app.post("/predict")
        async def predict(
            request: PredictRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)

            if not self.authMiddleware.checkRateLimit(apiKey):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            deployment = self.db.getDeployment(request.deploymentId)
            if not deployment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deployment not found"
                )

            if deployment.userId != apiKey.userId:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

            startTime = time.time()
            model = self.modelManager.getModel(
                deployment.modelName,
                deployment.config
            )

            predictionInput = PredictionInput(
                data=request.data,
                options=request.options
            )

            result = model.predict(predictionInput)
            processingTimeMs = (time.time() - startTime) * 1000

            self.usageTracker.trackRequest(
                userId=apiKey.userId,
                deploymentId=deployment.deploymentId,
                modelName=deployment.modelName,
                processingTimeMs=processingTimeMs
            )

            self.apiKeyManager.incrementUsage(apiKey.keyId)

            return result.dict()

        @self.app.post("/api-keys")
        async def createApiKey(
            request: CreateApiKeyRequest,
            userId: str
        ):
            fullKey, apiKey = self.apiKeyManager.generateKey(
                userId=userId,
                name=request.name,
                expiresInDays=request.expiresInDays,
                rateLimit=request.rateLimit,
                permissions={'predict': True, 'deploy': True}
            )

            return {
                "apiKey": fullKey,
                "metadata": apiKey.dict(exclude={'keyHash'}),
                "warning": "Save this key securely. It won't be shown again."
            }

        @self.app.get("/api-keys")
        async def listApiKeys(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)
            keys = self.apiKeyManager.listKeys(apiKey.userId)

            return {
                "apiKeys": [k.dict(exclude={'keyHash'}) for k in keys]
            }

        @self.app.delete("/api-keys/{keyId}")
        async def revokeApiKey(
            keyId: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)
            success = self.apiKeyManager.revokeKey(keyId)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )

            return {"message": "API key revoked successfully"}

        @self.app.get("/usage")
        async def getUsage(
            credentials: HTTPAuthorizationCredentials = Depends(self.security),
            startDate: Optional[str] = None,
            endDate: Optional[str] = None
        ):
            apiKey = await self.authMiddleware.authenticate(credentials)

            start = datetime.fromisoformat(startDate) if startDate else None
            end = datetime.fromisoformat(endDate) if endDate else None

            usage = self.usageTracker.getUserCosts(apiKey.userId, start, end)
            return usage

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
