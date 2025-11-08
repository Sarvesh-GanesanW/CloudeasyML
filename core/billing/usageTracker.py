from datetime import datetime
from typing import Dict, Any
import uuid
from core.database.models import UsageRecord
from core.database.databaseManager import DatabaseManager

class UsageTracker:
    def __init__(self, database: DatabaseManager, pricingEngine):
        self.db = database
        self.pricingEngine = pricingEngine

    def trackRequest(self, userId: str, deploymentId: str,
                    modelName: str, processingTimeMs: float,
                    metadata: Dict[str, Any] = {}) -> UsageRecord:
        cost = self.pricingEngine.calculateCost(
            modelName=modelName,
            processingTimeMs=processingTimeMs,
            requestCount=1
        )

        record = UsageRecord(
            recordId=str(uuid.uuid4()),
            userId=userId,
            deploymentId=deploymentId,
            modelName=modelName,
            processingTimeMs=processingTimeMs,
            cost=cost,
            metadata=metadata
        )

        self.db.saveUsageRecord(record)
        return record

    def getUserCosts(self, userId: str, startDate: datetime = None,
                    endDate: datetime = None) -> Dict[str, Any]:
        records = self.db.getUserUsage(userId, startDate, endDate)

        totalCost = sum(r.cost for r in records)
        totalRequests = len(records)
        totalProcessingTime = sum(r.processingTimeMs for r in records)

        byModel = {}
        for record in records:
            if record.modelName not in byModel:
                byModel[record.modelName] = {
                    'requests': 0,
                    'cost': 0.0,
                    'processingTimeMs': 0.0
                }
            byModel[record.modelName]['requests'] += 1
            byModel[record.modelName]['cost'] += record.cost
            byModel[record.modelName]['processingTimeMs'] += record.processingTimeMs

        return {
            'userId': userId,
            'totalCost': totalCost,
            'totalRequests': totalRequests,
            'totalProcessingTimeMs': totalProcessingTime,
            'byModel': byModel,
            'period': {
                'startDate': startDate,
                'endDate': endDate
            }
        }
