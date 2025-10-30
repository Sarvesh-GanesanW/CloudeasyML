import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, SAGEConv, GATConv
from torch_geometric.data import Data
import numpy as np
from typing import Optional, Tuple


class SpatialEncoder(nn.Module):
    def __init__(
        self,
        inChannels: int,
        hiddenChannels: int,
        outChannels: int,
        aggregation: str = "graphsage",
        dropout: float = 0.3,
    ):
        super(SpatialEncoder, self).__init__()
        self.aggregation = aggregation
        self.dropout = dropout

        if aggregation == "gcn":
            self.conv1 = GCNConv(inChannels, hiddenChannels)
            self.conv2 = GCNConv(hiddenChannels, outChannels)
        elif aggregation == "graphsage":
            self.conv1 = SAGEConv(inChannels, hiddenChannels)
            self.conv2 = SAGEConv(hiddenChannels, outChannels)
        elif aggregation == "gat":
            self.conv1 = GATConv(inChannels, hiddenChannels)
            self.conv2 = GATConv(hiddenChannels, outChannels)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

    def forward(self, x: torch.Tensor, edgeIndex: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edgeIndex)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edgeIndex)
        return x


class TemporalEncoder(nn.Module):
    def __init__(
        self, inputSize: int, hiddenSize: int, numLayers: int = 2, dropout: float = 0.3
    ):
        super(TemporalEncoder, self).__init__()
        self.hiddenSize = hiddenSize
        self.numLayers = numLayers

        self.gru = nn.GRU(
            input_size=inputSize,
            hidden_size=hiddenSize,
            num_layers=numLayers,
            batch_first=True,
            dropout=dropout if numLayers > 1 else 0,
        )

    def forward(
        self, x: torch.Tensor, hidden: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        output, hidden = self.gru(x, hidden)
        return output, hidden


class STGNNModel(nn.Module):
    def __init__(
        self,
        numNodes: int,
        nodeFeatures: int,
        hiddenChannels: int = 128,
        numLayers: int = 3,
        dropout: float = 0.3,
        spatialAggregation: str = "graphsage",
        forecastHorizon: int = 12,
    ):
        super(STGNNModel, self).__init__()

        self.numNodes = numNodes
        self.nodeFeatures = nodeFeatures
        self.hiddenChannels = hiddenChannels
        self.forecastHorizon = forecastHorizon

        self.spatialEncoder = SpatialEncoder(
            inChannels=nodeFeatures,
            hiddenChannels=hiddenChannels,
            outChannels=hiddenChannels,
            aggregation=spatialAggregation,
            dropout=dropout,
        )

        self.temporalEncoder = TemporalEncoder(
            inputSize=hiddenChannels,
            hiddenSize=hiddenChannels,
            numLayers=numLayers,
            dropout=dropout,
        )

        self.attentionWeight = nn.Linear(hiddenChannels, 1)

        self.decoder = nn.Sequential(
            nn.Linear(hiddenChannels, hiddenChannels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hiddenChannels, forecastHorizon),
        )

    def forward(
        self, x: torch.Tensor, edgeIndex: torch.Tensor, temporalLength: int
    ) -> torch.Tensor:
        batchSize = x.shape[0] // self.numNodes

        spatialFeatures = []
        for t in range(temporalLength):
            startIdx = t * self.numNodes
            endIdx = (t + 1) * self.numNodes
            xt = x[startIdx:endIdx]

            spatialOut = self.spatialEncoder(xt, edgeIndex)
            spatialFeatures.append(spatialOut)

        spatialFeaturesTensor = torch.stack(spatialFeatures, dim=1)

        temporalOut, _ = self.temporalEncoder(spatialFeaturesTensor)

        attentionScores = self.attentionWeight(temporalOut)
        attentionWeights = F.softmax(attentionScores, dim=1)
        contextVector = (temporalOut * attentionWeights).sum(dim=1)

        predictions = self.decoder(contextVector)

        return predictions


class STGNNForecaster:
    def __init__(
        self,
        numNodes: int,
        nodeFeatures: int,
        hiddenChannels: int = 128,
        numLayers: int = 3,
        dropout: float = 0.3,
        spatialAggregation: str = "graphsage",
        forecastHorizon: int = 12,
        device: str = "cuda",
    ):
        self.device = device if torch.cuda.is_available() else "cpu"

        self.model = STGNNModel(
            numNodes=numNodes,
            nodeFeatures=nodeFeatures,
            hiddenChannels=hiddenChannels,
            numLayers=numLayers,
            dropout=dropout,
            spatialAggregation=spatialAggregation,
            forecastHorizon=forecastHorizon,
        ).to(self.device)

        self.optimizer = None
        self.criterion = nn.MSELoss()

    def initOptimizer(self, learningRate: float = 0.001, weightDecay: float = 1e-5):
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=learningRate, weight_decay=weightDecay
        )

    def train(
        self,
        x: torch.Tensor,
        edgeIndex: torch.Tensor,
        y: torch.Tensor,
        temporalLength: int,
        epochs: int = 100,
    ):
        if self.optimizer is None:
            self.initOptimizer()

        self.model.train()
        losses = []

        x = x.to(self.device)
        edgeIndex = edgeIndex.to(self.device)
        y = y.to(self.device)

        for epoch in range(epochs):
            self.optimizer.zero_grad()

            predictions = self.model(x, edgeIndex, temporalLength)
            loss = self.criterion(predictions, y)

            loss.backward()
            self.optimizer.step()

            losses.append(loss.item())

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item():.4f}")

        return losses

    def predict(
        self, x: torch.Tensor, edgeIndex: torch.Tensor, temporalLength: int
    ) -> np.ndarray:
        self.model.eval()

        x = x.to(self.device)
        edgeIndex = edgeIndex.to(self.device)

        with torch.no_grad():
            predictions = self.model(x, edgeIndex, temporalLength)

        return predictions.cpu().numpy()

    def saveModel(self, path: str):
        torch.save(self.model.state_dict(), path)

    def loadModel(self, path: str):
        self.model.load_state_dict(torch.load(path))
