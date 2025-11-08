from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from pathlib import Path
from .models import User, Deployment, UsageRecord
from core.auth.apiKeyManager import ApiKey

class DatabaseManager:
    def __init__(self, dbPath: str = "data/db"):
        self.dbPath = Path(dbPath)
        self.dbPath.mkdir(parents=True, exist_ok=True)
        self.usersPath = self.dbPath / "users.json"
        self.apiKeysPath = self.dbPath / "apiKeys.json"
        self.deploymentsPath = self.dbPath / "deployments.json"
        self.usagePath = self.dbPath / "usage.json"

        self._initializeFiles()

    def _initializeFiles(self) -> None:
        for path in [self.usersPath, self.apiKeysPath,
                     self.deploymentsPath, self.usagePath]:
            if not path.exists():
                path.write_text("[]")

    def _readJson(self, path: Path) -> List[Dict]:
        return json.loads(path.read_text())

    def _writeJson(self, path: Path, data: List[Dict]) -> None:
        path.write_text(json.dumps(data, indent=2, default=str))

    def saveUser(self, user: User) -> None:
        users = self._readJson(self.usersPath)
        users = [u for u in users if u['userId'] != user.userId]
        users.append(user.dict())
        self._writeJson(self.usersPath, users)

    def getUser(self, userId: str) -> Optional[User]:
        users = self._readJson(self.usersPath)
        for user in users:
            if user['userId'] == userId:
                return User(**user)
        return None

    def saveApiKey(self, apiKey: ApiKey) -> None:
        keys = self._readJson(self.apiKeysPath)
        keys = [k for k in keys if k['keyId'] != apiKey.keyId]
        keys.append(apiKey.dict())
        self._writeJson(self.apiKeysPath, keys)

    def getApiKey(self, keyId: str) -> Optional[ApiKey]:
        keys = self._readJson(self.apiKeysPath)
        for key in keys:
            if key['keyId'] == keyId:
                return ApiKey(**key)
        return None

    def incrementApiKeyUsage(self, keyId: str) -> None:
        keys = self._readJson(self.apiKeysPath)
        for key in keys:
            if key['keyId'] == keyId:
                key['usageCount'] = key.get('usageCount', 0) + 1
        self._writeJson(self.apiKeysPath, keys)

    def revokeApiKey(self, keyId: str) -> bool:
        keys = self._readJson(self.apiKeysPath)
        found = False
        for key in keys:
            if key['keyId'] == keyId:
                key['isActive'] = False
                found = True
        if found:
            self._writeJson(self.apiKeysPath, keys)
        return found

    def getUserApiKeys(self, userId: str) -> List[ApiKey]:
        keys = self._readJson(self.apiKeysPath)
        userKeys = [ApiKey(**k) for k in keys if k['userId'] == userId]
        return userKeys

    def saveDeployment(self, deployment: Deployment) -> None:
        deployments = self._readJson(self.deploymentsPath)
        deployments = [d for d in deployments
                      if d['deploymentId'] != deployment.deploymentId]
        deployments.append(deployment.dict())
        self._writeJson(self.deploymentsPath, deployments)

    def getDeployment(self, deploymentId: str) -> Optional[Deployment]:
        deployments = self._readJson(self.deploymentsPath)
        for deployment in deployments:
            if deployment['deploymentId'] == deploymentId:
                return Deployment(**deployment)
        return None

    def getUserDeployments(self, userId: str) -> List[Deployment]:
        deployments = self._readJson(self.deploymentsPath)
        userDeployments = [Deployment(**d) for d in deployments
                          if d['userId'] == userId]
        return userDeployments

    def saveUsageRecord(self, record: UsageRecord) -> None:
        records = self._readJson(self.usagePath)
        records.append(record.dict())
        self._writeJson(self.usagePath, records)

    def getUserUsage(self, userId: str, startDate: Optional[datetime] = None,
                    endDate: Optional[datetime] = None) -> List[UsageRecord]:
        records = self._readJson(self.usagePath)
        userRecords = [UsageRecord(**r) for r in records if r['userId'] == userId]

        if startDate:
            userRecords = [r for r in userRecords if r.timestamp >= startDate]
        if endDate:
            userRecords = [r for r in userRecords if r.timestamp <= endDate]

        return userRecords
