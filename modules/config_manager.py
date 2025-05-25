import configparser
import os
from loguru import logger

class ConfigManager:
    """
    Manage configuration settings from a config.ini file.
    """
    def __init__(self, config_file='config.ini'):
        """
        Initialize the ConfigManager with a configuration file.

        Args:
            config_file (str): Path to the configuration file (default: 'config.ini').
        """
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        if os.path.exists(config_file):
            self.config.read(config_file)
            logger.info(f"Loaded configuration from {config_file}")
        else:
            self.config = None
            logger.warning(f"Configuration file {config_file} not found")

    def get_int(self, section, key, fallback):
        """
        Get an integer value from the configuration.

        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            fallback (int): Default value if key is not found or invalid.

        Returns:
            int: The configuration value or fallback.
        """
        try:
            if self.config and section in self.config:
                return int(self.config[section][key])
            return fallback
        except (KeyError, ValueError) as e:
            logger.warning(f"Error reading {section}.{key}, using fallback: {fallback}. Error: {e}")
            return fallback

    def get_float(self, section, key, fallback):
        """
        Get a float value from the configuration.

        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            fallback (float): Default value if key is not found or invalid.

        Returns:
            float: The configuration value or fallback.
        """
        try:
            if self.config and section in self.config:
                return float(self.config[section][key])
            return fallback
        except (KeyError, ValueError) as e:
            logger.warning(f"Error reading {section}.{key}, using fallback: {fallback}. Error: {e}")
            return fallback

    def get_bool(self, section, key, fallback):
        """
        Get a boolean value from the configuration.

        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            fallback (bool): Default value if key is not found or invalid.

        Returns:
            bool: The configuration value or fallback.
        """
        try:
            if self.config and section in self.config:
                return self.config.getboolean(section, key)
            return fallback
        except (KeyError, ValueError) as e:
            logger.warning(f"Error reading {section}.{key}, using fallback: {fallback}. Error: {e}")
            return fallback

    def get_string(self, section, key, fallback):
        """
        Get a string value from the configuration.

        Args:
            section (str): Configuration section.
            key (str): Configuration key.
            fallback (str): Default value if key is not found or invalid.

        Returns:
            str: The configuration value or fallback.
        """
        try:
            if self.config and section in self.config:
                return self.config[section][key]
            return fallback
        except (KeyError, ValueError) as e:
            logger.warning(f"Error reading {section}.{key}, using fallback: {fallback}. Error: {e}")
            return fallback