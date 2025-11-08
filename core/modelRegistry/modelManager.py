from typing import Dict, List, Optional, Type
from .baseModel import BaseModel, ModelMetadata
import importlib
import inspect
from pathlib import Path

class ModelManager:
    def __init__(self, pluginsPath: str = "plugins"):
        self.pluginsPath = Path(pluginsPath)
        self.registeredModels: Dict[str, Type[BaseModel]] = {}
        self.loadedModels: Dict[str, BaseModel] = {}

    def discoverPlugins(self) -> List[str]:
        plugins = []
        if not self.pluginsPath.exists():
            return plugins

        for pluginDir in self.pluginsPath.iterdir():
            if pluginDir.is_dir() and (pluginDir / "model.py").exists():
                plugins.append(pluginDir.name)
        return plugins

    def registerModel(self, modelName: str, modelClass: Type[BaseModel]) -> None:
        if not issubclass(modelClass, BaseModel):
            raise ValueError(f"{modelClass} must inherit from BaseModel")
        self.registeredModels[modelName] = modelClass

    def loadPlugin(self, pluginName: str) -> None:
        try:
            modulePath = f"{self.pluginsPath.name}.{pluginName}.model"
            module = importlib.import_module(modulePath)

            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseModel) and
                    obj != BaseModel):
                    self.registerModel(pluginName, obj)
                    break
        except Exception as e:
            raise RuntimeError(f"Failed to load plugin {pluginName}: {str(e)}")

    def loadAllPlugins(self) -> None:
        plugins = self.discoverPlugins()
        for plugin in plugins:
            try:
                self.loadPlugin(plugin)
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin}: {str(e)}")

    def createModel(self, modelName: str, config: Dict) -> BaseModel:
        if modelName not in self.registeredModels:
            raise ValueError(f"Model {modelName} not registered")

        modelClass = self.registeredModels[modelName]
        model = modelClass(config)
        return model

    def getModel(self, modelName: str, config: Optional[Dict] = None) -> BaseModel:
        if modelName not in self.loadedModels:
            if config is None:
                config = {}
            model = self.createModel(modelName, config)
            model.load()
            self.loadedModels[modelName] = model
        return self.loadedModels[modelName]

    def unloadModel(self, modelName: str) -> None:
        if modelName in self.loadedModels:
            self.loadedModels[modelName].unload()
            del self.loadedModels[modelName]

    def listModels(self) -> List[ModelMetadata]:
        metadata = []
        for modelName, modelClass in self.registeredModels.items():
            tempModel = modelClass({})
            metadata.append(tempModel.getMetadata())
        return metadata
