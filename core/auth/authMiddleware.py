from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .apiKeyManager import ApiKeyManager, ApiKey

class AuthMiddleware:
    def __init__(self, apiKeyManager: ApiKeyManager):
        self.apiKeyManager = apiKeyManager
        self.security = HTTPBearer()

    async def authenticate(self, credentials: HTTPAuthorizationCredentials) -> ApiKey:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials"
            )

        apiKey = self.apiKeyManager.validateKey(credentials.credentials)
        if not apiKey:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key"
            )

        return apiKey

    def checkPermission(self, apiKey: ApiKey, permission: str) -> bool:
        return apiKey.permissions.get(permission, False)

    def checkRateLimit(self, apiKey: ApiKey) -> bool:
        return apiKey.usageCount < apiKey.rateLimit
