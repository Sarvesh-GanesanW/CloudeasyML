import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.configLoader import ConfigLoader


class CrisisDetector:
    def __init__(self, configPath: str = "config/config.yaml"):
        self.config = ConfigLoader(configPath)
        self.predictionConfig = self.config.getPredictionConfig()

        self.thresholds = {
            "high": self.predictionConfig["crisisThresholdHigh"],
            "medium": self.predictionConfig["crisisThresholdMedium"],
        }

    def detectCrisisLevel(
        self, predictions: np.ndarray, historical: np.ndarray
    ) -> Dict:
        percentChange = ((predictions - historical[-1]) / historical[-1]) * 100

        volatility = np.std(predictions)
        historicalVolatility = np.std(historical[-12:])
        volatilityIncrease = (volatility / historicalVolatility) - 1

        priceDeclineRisk = np.mean(percentChange < -10)
        rapidAppreciationRisk = np.mean(percentChange > 20)

        crisisScore = (
            0.4 * priceDeclineRisk
            + 0.3 * rapidAppreciationRisk
            + 0.3 * min(volatilityIncrease, 1.0)
        )

        if crisisScore >= self.thresholds["high"]:
            level = "HIGH"
        elif crisisScore >= self.thresholds["medium"]:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "crisisLevel": level,
            "crisisScore": crisisScore,
            "priceDeclineRisk": priceDeclineRisk,
            "rapidAppreciationRisk": rapidAppreciationRisk,
            "volatilityIncrease": volatilityIncrease,
            "percentChange": percentChange,
        }

    def generateRecommendations(self, crisisAnalysis: Dict) -> List[str]:
        recommendations = []
        level = crisisAnalysis["crisisLevel"]

        if level == "HIGH":
            recommendations.extend(
                [
                    "EMERGENCY: Implement dynamic rent control mechanisms",
                    "Activate emergency housing voucher programs",
                    "Fast-track development approvals in high-demand areas",
                    "Increase affordable housing supply through public-private partnerships",
                    "Monitor market daily for rapid intervention",
                ]
            )
        elif level == "MEDIUM":
            recommendations.extend(
                [
                    "PREVENTIVE: Optimize zoning regulations for increased density",
                    "Identify development sites through spatial analysis",
                    "Implement targeted housing subsidies for at-risk populations",
                    "Enhance monitoring frequency to weekly assessments",
                    "Prepare contingency plans for potential escalation",
                ]
            )
        else:
            recommendations.extend(
                [
                    "OPTIMIZATION: Continue routine market monitoring",
                    "Refine predictive models with latest data",
                    "Conduct policy impact simulations",
                    "Analyze long-term market trends",
                    "Maintain early warning system vigilance",
                ]
            )

        if crisisAnalysis["priceDeclineRisk"] > 0.3:
            recommendations.append(
                "WARNING: High probability of significant price decline - prepare market stabilization measures"
            )

        if crisisAnalysis["rapidAppreciationRisk"] > 0.3:
            recommendations.append(
                "WARNING: Rapid price appreciation detected - implement affordability preservation strategies"
            )

        if crisisAnalysis["volatilityIncrease"] > 0.5:
            recommendations.append(
                "ALERT: Market volatility increasing - enhance risk monitoring protocols"
            )

        return recommendations


class PredictionPipeline:
    def __init__(self, models: Dict, configPath: str = "config/config.yaml"):
        self.models = models
        self.config = ConfigLoader(configPath)
        self.crisisDetector = CrisisDetector(configPath)

    def predictWithEnsemble(self, X: pd.DataFrame) -> np.ndarray:
        if "autoGluon" in self.models:
            return self.models["autoGluon"].predict(X)
        elif "stackedEnsemble" in self.models:
            return self.models["stackedEnsemble"].predict(X)
        elif "gradientBoosting" in self.models:
            return self.models["gradientBoosting"].predict(X)
        else:
            raise ValueError("No trained ensemble model found")

    def generateForecast(
        self, X: pd.DataFrame, historicalData: np.ndarray, horizon: int = 12
    ) -> Dict:
        predictions = self.predictWithEnsemble(X)

        crisisAnalysis = self.crisisDetector.detectCrisisLevel(
            predictions, historicalData
        )

        recommendations = self.crisisDetector.generateRecommendations(crisisAnalysis)

        return {
            "predictions": predictions,
            "horizon": horizon,
            "crisisAnalysis": crisisAnalysis,
            "recommendations": recommendations,
        }

    def generateReport(
        self, forecastResult: Dict, targetName: str = "Housing Price Index"
    ) -> str:
        report = []
        report.append("=" * 70)
        report.append("HOUSING CRISIS PREDICTION REPORT")
        report.append("=" * 70)
        report.append(f"\nTarget: {targetName}")
        report.append(f"Forecast Horizon: {forecastResult['horizon']} months")

        crisis = forecastResult["crisisAnalysis"]
        report.append(f"\n{'=' * 70}")
        report.append("CRISIS ASSESSMENT")
        report.append(f"{'=' * 70}")
        report.append(f"Crisis Level: {crisis['crisisLevel']}")
        report.append(f"Crisis Score: {crisis['crisisScore']:.3f}")
        report.append(f"Price Decline Risk: {crisis['priceDeclineRisk']:.1%}")
        report.append(f"Rapid Appreciation Risk: {crisis['rapidAppreciationRisk']:.1%}")
        report.append(f"Volatility Increase: {crisis['volatilityIncrease']:.1%}")

        report.append(f"\n{'=' * 70}")
        report.append("POLICY RECOMMENDATIONS")
        report.append(f"{'=' * 70}")
        for i, rec in enumerate(forecastResult["recommendations"], 1):
            report.append(f"{i}. {rec}")

        report.append(f"\n{'=' * 70}")
        report.append("FORECAST SUMMARY")
        report.append(f"{'=' * 70}")
        preds = forecastResult["predictions"]
        report.append(f"Mean Predicted Value: {np.mean(preds):.2f}")
        report.append(f"Predicted Range: [{np.min(preds):.2f}, {np.max(preds):.2f}]")
        report.append(f"Predicted Std Dev: {np.std(preds):.2f}")

        report.append(f"\n{'=' * 70}")

        return "\n".join(report)

    def runPrediction(
        self,
        testX: pd.DataFrame,
        historicalY: np.ndarray,
        targetName: str = "Housing Price Index",
    ) -> Dict:
        print("Generating forecasts...")

        forecastResult = self.generateForecast(testX, historicalY)

        report = self.generateReport(forecastResult, targetName)
        print(report)

        return forecastResult
