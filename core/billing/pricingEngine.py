from typing import Dict

class PricingEngine:
    def __init__(self, pricingConfig: Dict[str, Dict] = None):
        self.pricingConfig = pricingConfig or self._getDefaultPricing()

    def _getDefaultPricing(self) -> Dict[str, Dict]:
        return {
            'default': {
                'perRequest': 0.001,
                'perSecond': 0.0001,
                'perGpuHour': 0.5
            },
            'housingCrisis': {
                'perRequest': 0.002,
                'perSecond': 0.0002,
                'perGpuHour': 0.5
            }
        }

    def calculateCost(self, modelName: str, processingTimeMs: float,
                     requestCount: int = 1, gpuHours: float = 0) -> float:
        pricing = self.pricingConfig.get(
            modelName,
            self.pricingConfig['default']
        )

        requestCost = pricing['perRequest'] * requestCount
        timeCost = pricing['perSecond'] * (processingTimeMs / 1000.0)
        gpuCost = pricing['perGpuHour'] * gpuHours

        return requestCost + timeCost + gpuCost

    def updatePricing(self, modelName: str, pricing: Dict[str, float]) -> None:
        self.pricingConfig[modelName] = pricing

    def getPricing(self, modelName: str = None) -> Dict:
        if modelName:
            return self.pricingConfig.get(modelName, self.pricingConfig['default'])
        return self.pricingConfig
