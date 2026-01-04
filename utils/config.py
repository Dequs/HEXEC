import json
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="logs.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class Config:
    def __init__(self, configPath='config.json'):
        logger.info(f"Initializing Config with path: {configPath}")
        self.configPath = configPath
        self.config = self.loadConfig()

    def loadConfig(self):
        logger.info("Loading configuration from file.")
        try:
            with open(self.configPath, 'r') as file:
                logger.info("Config file found.")
                return json.load(file)
        except FileNotFoundError:
            logger.warning("Config file not found, using default settings.")
            print("Config file not found, using default settings.")
            return {}
        except json.JSONDecodeError:
            logger.error("Error decoding config file, using default settings.")
            print("Error decoding config file, using default settings.")
            return {}
        
    def createConfig(self, settings: dict):
        logger.info("Creating new configuration file.")
        with open(self.configPath, 'w') as file:
            json.dump(settings, file, indent=4)
        self.config = settings
        logger.info("Configuration file created successfully.")

    def get(self, key, default=None):
        logger.info(f"Retrieving config value for key: {key}")
        return self.config.get(key, default)