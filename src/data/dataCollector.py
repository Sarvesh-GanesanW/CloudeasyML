import pandas as pd
import numpy as np
from fredapi import Fred
import requests
from pathlib import Path
from typing import List, Dict, Optional
import pickle
from datetime import datetime


class DataCollector:
    def __init__(self, fredApiKey: Optional[str] = None, cachePath: str = "data/cache"):
        self.fredApiKey = fredApiKey
        self.cachePath = Path(cachePath)
        self.cachePath.mkdir(parents=True, exist_ok=True)

        if fredApiKey:
            self.fredClient = Fred(api_key=fredApiKey)

    def collectFredData(
        self, seriesIds: List[str], startDate: str = "2010-01-01"
    ) -> pd.DataFrame:
        cacheFile = (
            self.cachePath
            / "fred"
            / f"fred_data_{datetime.now().strftime('%Y%m%d')}.pkl"
        )
        cacheFile.parent.mkdir(parents=True, exist_ok=True)

        if cacheFile.exists():
            with open(cacheFile, "rb") as f:
                return pickle.load(f)

        dataFrames = {}
        for seriesId in seriesIds:
            try:
                data = self.fredClient.get_series(seriesId, observation_start=startDate)
                dataFrames[seriesId] = data
            except Exception as e:
                print(f"Error fetching {seriesId}: {e}")

        combinedDf = pd.DataFrame(dataFrames)

        with open(cacheFile, "wb") as f:
            pickle.dump(combinedDf, f)

        return combinedDf

    def collectZillowData(self, region: str = "national") -> pd.DataFrame:
        cacheFile = self.cachePath / "zillow" / f"zillow_{region}.pkl"
        cacheFile.parent.mkdir(parents=True, exist_ok=True)

        if cacheFile.exists():
            with open(cacheFile, "rb") as f:
                return pickle.load(f)

        zillowFredSeries = [
            "ZHVI",
            "ZRIP",
            "ZSFH",
        ]

        if self.fredApiKey:
            zillowData = self.collectFredData(zillowFredSeries)

            with open(cacheFile, "wb") as f:
                pickle.dump(zillowData, f)

            return zillowData

        return pd.DataFrame()

    def getEconomicIndicators(self) -> List[str]:
        return [
            "GDP",
            "CPIAUCSL",
            "UNRATE",
            "FEDFUNDS",
            "MORTGAGE30US",
            "HOUST",
            "PERMIT",
            "MSACSR",
            "RRVRUSQ156N",
            "CSUSHPISA",
            "MSPUS",
            "USSTHPI",
        ]

    def collectAllData(self, startDate: str = "2010-01-01") -> Dict[str, pd.DataFrame]:
        economicData = self.collectFredData(self.getEconomicIndicators(), startDate)
        housingData = self.collectZillowData()

        return {"economic": economicData, "housing": housingData}
