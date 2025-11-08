from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import hashlib
from pydantic import BaseModel

class ApiKey(BaseModel):
    keyId: str
    keyHash: str
    userId: str
    name: str
    createdAt: datetime
    expiresAt: Optional[datetime] = None
    isActive: bool = True
    permissions: Dict[str, bool] = {}
    rateLimit: int = 1000
    usageCount: int = 0

class ApiKeyManager:
    def __init__(self, database):
        self.db = database

    def generateKey(self, userId: str, name: str,
                   expiresInDays: Optional[int] = None,
                   permissions: Optional[Dict[str, bool]] = None,
                   rateLimit: int = 1000) -> tuple[str, ApiKey]:
        keyId = f"sk_{secrets.token_urlsafe(16)}"
        keySecret = secrets.token_urlsafe(32)
        fullKey = f"{keyId}.{keySecret}"

        keyHash = hashlib.sha256(keySecret.encode()).hexdigest()

        expiresAt = None
        if expiresInDays:
            expiresAt = datetime.now() + timedelta(days=expiresInDays)

        apiKey = ApiKey(
            keyId=keyId,
            keyHash=keyHash,
            userId=userId,
            name=name,
            createdAt=datetime.now(),
            expiresAt=expiresAt,
            permissions=permissions or {},
            rateLimit=rateLimit
        )

        self.db.saveApiKey(apiKey)
        return fullKey, apiKey

    def validateKey(self, fullKey: str) -> Optional[ApiKey]:
        try:
            keyId, keySecret = fullKey.split('.')
            keyHash = hashlib.sha256(keySecret.encode()).hexdigest()

            apiKey = self.db.getApiKey(keyId)
            if not apiKey:
                return None

            if apiKey.keyHash != keyHash:
                return None

            if not apiKey.isActive:
                return None

            if apiKey.expiresAt and apiKey.expiresAt < datetime.now():
                return None

            return apiKey
        except:
            return None

    def incrementUsage(self, keyId: str) -> None:
        self.db.incrementApiKeyUsage(keyId)

    def revokeKey(self, keyId: str) -> bool:
        return self.db.revokeApiKey(keyId)

    def listKeys(self, userId: str) -> list[ApiKey]:
        return self.db.getUserApiKeys(userId)
