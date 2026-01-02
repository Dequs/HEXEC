import json
from utils.client import AI

class Config:
    def __init__(self, configPath='config.json'):
        self.configPath = configPath
        self.config = self.loadConfig()

    def loadConfig(self):
        try:
            with open(self.configPath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Config file not found, using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error decoding config file, using default settings.")
            return {}
        
    def createConfig(self, settings: dict):
        with open(self.configPath, 'w') as file:
            json.dump(settings, file, indent=4)
        self.config = settings

    def get(self, key, default=None):
        return self.config.get(key, default)