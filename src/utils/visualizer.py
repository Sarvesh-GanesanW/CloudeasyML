import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px


class Visualizer:
    def __init__(self, style: str = "seaborn-v0_8-darkgrid"):
        plt.style.use(style)
        sns.set_palette("husl")

    def plotTimeSeries(
        self,
        data: pd.DataFrame,
        columns: List[str],
        title: str = "Time Series Data",
        figsize: tuple = (15, 8),
    ):
        fig, axes = plt.subplots(len(columns), 1, figsize=figsize, sharex=True)

        if len(columns) == 1:
            axes = [axes]

        for i, col in enumerate(columns):
            axes[i].plot(data.index, data[col], linewidth=2)
            axes[i].set_ylabel(col, fontsize=10)
            axes[i].grid(True, alpha=0.3)

        axes[0].set_title(title, fontsize=14, fontweight="bold")
        axes[-1].set_xlabel("Date", fontsize=10)

        plt.tight_layout()
        return fig

    def plotPredictionsVsActual(
        self,
        actual: np.ndarray,
        predicted: np.ndarray,
        title: str = "Predictions vs Actual",
        figsize: tuple = (12, 6),
    ):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        ax1.plot(actual, label="Actual", linewidth=2, alpha=0.7)
        ax1.plot(predicted, label="Predicted", linewidth=2, alpha=0.7)
        ax1.set_xlabel("Time Step")
        ax1.set_ylabel("Value")
        ax1.set_title(f"{title} - Time Series")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.scatter(actual, predicted, alpha=0.6, edgecolors="k", linewidth=0.5)

        minVal = min(actual.min(), predicted.min())
        maxVal = max(actual.max(), predicted.max())
        ax2.plot(
            [minVal, maxVal],
            [minVal, maxVal],
            "r--",
            linewidth=2,
            label="Perfect Prediction",
        )

        ax2.set_xlabel("Actual")
        ax2.set_ylabel("Predicted")
        ax2.set_title(f"{title} - Scatter Plot")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plotFeatureImportance(
        self,
        importance: pd.DataFrame,
        top_n: int = 20,
        title: str = "Feature Importance",
        figsize: tuple = (12, 8),
    ):
        topFeatures = importance.head(top_n)

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.viridis(np.linspace(0, 1, len(topFeatures)))
        bars = ax.barh(range(len(topFeatures)), topFeatures["importance"], color=colors)

        ax.set_yticks(range(len(topFeatures)))
        ax.set_yticklabels(topFeatures["feature"])
        ax.invert_yaxis()
        ax.set_xlabel("Importance Score", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="x")

        plt.tight_layout()
        return fig

    def plotModelComparison(
        self,
        metrics: Dict[str, Dict],
        metricName: str = "rmse",
        title: str = "Model Comparison",
        figsize: tuple = (10, 6),
    ):
        modelNames = list(metrics.keys())
        values = [metrics[model].get(metricName, 0) for model in modelNames]

        fig, ax = plt.subplots(figsize=figsize)

        colors = plt.cm.Set3(np.linspace(0, 1, len(modelNames)))
        bars = ax.bar(
            modelNames, values, color=colors, edgecolor="black", linewidth=1.5
        )

        ax.set_ylabel(metricName.upper(), fontsize=12)
        ax.set_title(f"{title} - {metricName.upper()}", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.4f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        return fig

    def plotCrisisTimeline(
        self,
        predictions: np.ndarray,
        crisisScores: np.ndarray,
        thresholds: Dict[str, float],
        dates: Optional[pd.DatetimeIndex] = None,
        title: str = "Crisis Timeline",
        figsize: tuple = (15, 8),
    ):
        if dates is None:
            dates = pd.date_range(
                start="2024-01-01", periods=len(predictions), freq="MS"
            )

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

        ax1.plot(
            dates, predictions, linewidth=2, color="steelblue", label="Predictions"
        )
        ax1.fill_between(dates, predictions, alpha=0.3, color="steelblue")
        ax1.set_ylabel("Predicted Value", fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight="bold")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.plot(
            dates, crisisScores, linewidth=2, color="darkred", label="Crisis Score"
        )
        ax2.axhline(
            y=thresholds.get("high", 0.7),
            color="red",
            linestyle="--",
            linewidth=2,
            label="High Threshold",
        )
        ax2.axhline(
            y=thresholds.get("medium", 0.4),
            color="orange",
            linestyle="--",
            linewidth=2,
            label="Medium Threshold",
        )

        ax2.fill_between(
            dates,
            0,
            crisisScores,
            where=(crisisScores >= thresholds.get("high", 0.7)),
            color="red",
            alpha=0.3,
            label="High Risk",
        )
        ax2.fill_between(
            dates,
            0,
            crisisScores,
            where=(crisisScores >= thresholds.get("medium", 0.4))
            & (crisisScores < thresholds.get("high", 0.7)),
            color="orange",
            alpha=0.3,
            label="Medium Risk",
        )

        ax2.set_ylabel("Crisis Score", fontsize=12)
        ax2.set_xlabel("Date", fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def plotInteractiveForecast(
        self,
        historical: pd.Series,
        forecast: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray,
        title: str = "Interactive Forecast",
    ):
        forecastDates = pd.date_range(
            start=historical.index[-1], periods=len(forecast) + 1, freq="MS"
        )[1:]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=historical.index,
                y=historical.values,
                mode="lines",
                name="Historical",
                line=dict(color="steelblue", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecastDates,
                y=forecast,
                mode="lines",
                name="Forecast",
                line=dict(color="darkred", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecastDates.tolist() + forecastDates.tolist()[::-1],
                y=upper.tolist() + lower.tolist()[::-1],
                fill="toself",
                fillcolor="rgba(255,0,0,0.2)",
                line=dict(color="rgba(255,0,0,0)"),
                name="Confidence Interval",
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode="x unified",
            template="plotly_white",
            height=600,
        )

        return fig

    def plotSpatialHeatmap(
        self,
        data: pd.DataFrame,
        latCol: str,
        lonCol: str,
        valueCol: str,
        title: str = "Spatial Heatmap",
    ):
        fig = px.density_mapbox(
            data,
            lat=latCol,
            lon=lonCol,
            z=valueCol,
            radius=10,
            center=dict(lat=data[latCol].mean(), lon=data[lonCol].mean()),
            zoom=5,
            mapbox_style="open-street-map",
            title=title,
            height=600,
        )

        return fig

    def saveFigure(self, fig, filename: str, dpi: int = 300):
        if isinstance(fig, go.Figure):
            fig.write_html(filename)
        else:
            fig.savefig(filename, dpi=dpi, bbox_inches="tight")
        print(f"Figure saved to {filename}")
