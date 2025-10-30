import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
from typing import List, Tuple, Optional
from sklearn.metrics.pairwise import haversine_distances


class SpatialGraphBuilder:
    def __init__(self, distanceThreshold: float = 100.0, method: str = "knn"):
        self.distanceThreshold = distanceThreshold
        self.method = method

    def buildGraphFromCoordinates(
        self, coordinates: np.ndarray, k: int = 5
    ) -> torch.Tensor:
        numNodes = len(coordinates)

        if self.method == "knn":
            edges = self._buildKnnGraph(coordinates, k)
        elif self.method == "distance":
            edges = self._buildDistanceGraph(coordinates)
        elif self.method == "delaunay":
            edges = self._buildDelaunayGraph(coordinates)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        return edges

    def _buildKnnGraph(self, coordinates: np.ndarray, k: int) -> torch.Tensor:
        from sklearn.neighbors import NearestNeighbors

        nbrs = NearestNeighbors(n_neighbors=k + 1, metric="haversine")
        nbrs.fit(np.radians(coordinates))

        distances, indices = nbrs.kneighbors(np.radians(coordinates))

        edgeList = []
        for i in range(len(coordinates)):
            for j in range(1, k + 1):
                edgeList.append([i, indices[i][j]])
                edgeList.append([indices[i][j], i])

        edgeIndex = torch.tensor(edgeList, dtype=torch.long).t().contiguous()
        return edgeIndex

    def _buildDistanceGraph(self, coordinates: np.ndarray) -> torch.Tensor:
        coordsRad = np.radians(coordinates)
        distances = haversine_distances(coordsRad) * 6371

        edgeList = []
        numNodes = len(coordinates)

        for i in range(numNodes):
            for j in range(i + 1, numNodes):
                if distances[i, j] < self.distanceThreshold:
                    edgeList.append([i, j])
                    edgeList.append([j, i])

        edgeIndex = torch.tensor(edgeList, dtype=torch.long).t().contiguous()
        return edgeIndex

    def _buildDelaunayGraph(self, coordinates: np.ndarray) -> torch.Tensor:
        from scipy.spatial import Delaunay

        tri = Delaunay(coordinates)

        edgeSet = set()
        for simplex in tri.simplices:
            for i in range(3):
                for j in range(i + 1, 3):
                    edge = tuple(sorted([simplex[i], simplex[j]]))
                    edgeSet.add(edge)

        edgeList = []
        for edge in edgeSet:
            edgeList.append([edge[0], edge[1]])
            edgeList.append([edge[1], edge[0]])

        edgeIndex = torch.tensor(edgeList, dtype=torch.long).t().contiguous()
        return edgeIndex

    def buildGraphFromEconomicSimilarity(
        self, features: pd.DataFrame, threshold: float = 0.7
    ) -> torch.Tensor:
        from sklearn.metrics.pairwise import cosine_similarity

        similarity = cosine_similarity(features)

        edgeList = []
        numNodes = len(features)

        for i in range(numNodes):
            for j in range(i + 1, numNodes):
                if similarity[i, j] > threshold:
                    edgeList.append([i, j])
                    edgeList.append([j, i])

        edgeIndex = torch.tensor(edgeList, dtype=torch.long).t().contiguous()
        return edgeIndex

    def buildMultiRelationalGraph(
        self,
        spatialEdges: torch.Tensor,
        economicEdges: torch.Tensor,
        weights: Tuple[float, float] = (0.6, 0.4),
    ) -> torch.Tensor:
        allEdges = torch.cat([spatialEdges, economicEdges], dim=1)

        uniqueEdges = torch.unique(allEdges, dim=1)

        return uniqueEdges

    def createPyGData(
        self,
        nodeFeatures: np.ndarray,
        edgeIndex: torch.Tensor,
        labels: Optional[np.ndarray] = None,
    ) -> Data:
        x = torch.tensor(nodeFeatures, dtype=torch.float)

        data = Data(x=x, edge_index=edgeIndex)

        if labels is not None:
            data.y = torch.tensor(labels, dtype=torch.float)

        return data


class TemporalGraphBuilder:
    def __init__(self, snapshotInterval: int = 1):
        self.snapshotInterval = snapshotInterval

    def buildTemporalGraph(
        self,
        timeSeriesData: pd.DataFrame,
        spatialEdges: torch.Tensor,
        windowSize: int = 12,
    ) -> List[Data]:
        temporalGraphs = []

        numSnapshots = len(timeSeriesData) // self.snapshotInterval

        for t in range(windowSize, numSnapshots):
            windowData = timeSeriesData.iloc[
                (t - windowSize) * self.snapshotInterval : t * self.snapshotInterval
            ]

            aggregatedFeatures = windowData.groupby(level=0).mean().values

            graphData = Data(
                x=torch.tensor(aggregatedFeatures, dtype=torch.float),
                edge_index=spatialEdges,
                timestamp=t,
            )

            temporalGraphs.append(graphData)

        return temporalGraphs

    def addTemporalEdges(
        self, graphs: List[Data], connectionType: str = "consecutive"
    ) -> List[Data]:
        if connectionType == "consecutive":
            for i in range(len(graphs) - 1):
                graphs[i].next_timestamp = graphs[i + 1].timestamp

        return graphs
