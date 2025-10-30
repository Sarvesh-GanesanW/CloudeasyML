import yaml
from pathlib import Path


class ConfigLoader:
    def __init__(self, configPath="config/config.yaml"):
        self.configPath = Path(configPath)
        self.config = self._loadConfig()

    def _loadConfig(self):
        with open(self.configPath, "r") as file:
            return yaml.safe_load(file)

    def getDataConfig(self):
        return self.config["data"]

    def getModelConfig(self, modelName):
        return self.config["models"].get(modelName, {})

    def getEnsembleConfig(self):
        return self.config["ensemble"]

    def getTrainingConfig(self):
        return self.config["training"]

    def getPredictionConfig(self):
        return self.config["prediction"]
