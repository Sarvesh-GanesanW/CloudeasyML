import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import Tuple, Optional


class FeatureEngineer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.minMaxScaler = MinMaxScaler()
        self.featureNames = []

    def createTemporalFeatures(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if isinstance(df.index, pd.DatetimeIndex):
            df["month"] = df.index.month
            df["quarter"] = df.index.quarter
            df["year"] = df.index.year
            df["dayOfYear"] = df.index.dayofyear
            df["weekOfYear"] = df.index.isocalendar().week

        return df

    def createLagFeatures(
        self, df: pd.DataFrame, columns: list, lags: list = [1, 3, 6, 12]
    ) -> pd.DataFrame:
        df = df.copy()

        for col in columns:
            if col in df.columns:
                for lag in lags:
                    df[f"{col}_lag_{lag}"] = df[col].shift(lag)

        return df

    def createRollingFeatures(
        self, df: pd.DataFrame, columns: list, windows: list = [3, 6, 12]
    ) -> pd.DataFrame:
        df = df.copy()

        for col in columns:
            if col in df.columns:
                for window in windows:
                    df[f"{col}_rolling_mean_{window}"] = (
                        df[col].rolling(window=window).mean()
                    )
                    df[f"{col}_rolling_std_{window}"] = (
                        df[col].rolling(window=window).std()
                    )
                    df[f"{col}_rolling_min_{window}"] = (
                        df[col].rolling(window=window).min()
                    )
                    df[f"{col}_rolling_max_{window}"] = (
                        df[col].rolling(window=window).max()
                    )

        return df

    def createDifferenceFeatures(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        df = df.copy()

        for col in columns:
            if col in df.columns:
                df[f"{col}_diff_1"] = df[col].diff(1)
                df[f"{col}_diff_12"] = df[col].diff(12)
                df[f"{col}_pct_change_1"] = df[col].pct_change(1)
                df[f"{col}_pct_change_12"] = df[col].pct_change(12)

        return df

    def createInteractionFeatures(self, df: pd.DataFrame, pairs: list) -> pd.DataFrame:
        df = df.copy()

        for col1, col2 in pairs:
            if col1 in df.columns and col2 in df.columns:
                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
                df[f"{col1}_div_{col2}"] = df[col1] / (df[col2] + 1e-8)

        return df

    def engineerAllFeatures(
        self, df: pd.DataFrame, targetColumns: list
    ) -> pd.DataFrame:
        df = self.createTemporalFeatures(df)
        df = self.createLagFeatures(df, targetColumns)
        df = self.createRollingFeatures(df, targetColumns)
        df = self.createDifferenceFeatures(df, targetColumns)

        interactionPairs = [
            ("GDP", "UNRATE"),
            ("MORTGAGE30US", "HOUST"),
            ("FEDFUNDS", "CPIAUCSL"),
        ]
        df = self.createInteractionFeatures(df, interactionPairs)

        df = df.dropna()

        return df

    def scaleFeatures(self, X: pd.DataFrame, fit: bool = True) -> np.ndarray:
        if fit:
            return self.scaler.fit_transform(X)
        return self.scaler.transform(X)

    def splitTimeSeriesData(
        self,
        df: pd.DataFrame,
        targetCol: str,
        trainRatio: float = 0.7,
        valRatio: float = 0.15,
    ) -> Tuple:
        n = len(df)
        trainEnd = int(n * trainRatio)
        valEnd = int(n * (trainRatio + valRatio))

        featureCols = [col for col in df.columns if col != targetCol]

        trainX = df[featureCols].iloc[:trainEnd]
        trainY = df[targetCol].iloc[:trainEnd]

        valX = df[featureCols].iloc[trainEnd:valEnd]
        valY = df[targetCol].iloc[trainEnd:valEnd]

        testX = df[featureCols].iloc[valEnd:]
        testY = df[targetCol].iloc[valEnd:]

        return trainX, trainY, valX, valY, testX, testY
