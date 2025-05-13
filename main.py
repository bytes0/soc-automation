import yaml
import os


class ConfigParser:
    def __init__(self, config_file: str):
        """
        Initialize the ConfigParser with the path to the configuration file.

        :param config_file: Path to the YAML configuration file.
        """
        self.config_file = config_file
        self.config_data = None

    def load_config(self):
        """
        Load the configuration from a YAML file.

        :raises FileNotFoundError: If the configuration file does not exist.
        :raises ValueError: If there is an error parsing the YAML file.
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")

        try:
            with open(self.config_file, 'r') as file:
                self.config_data = yaml.safe_load(file)
            print(f"[+] Successfully loaded config from {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file '{self.config_file}': {str(e)}")

    def get(self, key: str, default=None):
        """
        Get a value from the loaded configuration data by key.

        :param key: The key to look for in the configuration data.
        :param default: The default value to return if the key is not found.
        :return: The value associated with the key, or the default if not found.
        :raises ValueError: If the config hasn't been loaded yet.
        """
        if self.config_data is None:
            raise ValueError("Configuration has not been loaded yet.")

        return self.config_data.get(key, default)

    def __repr__(self):
        """
        Return a string representation of the loaded config data.
        """
        return f"ConfigParser(config_file={self.config_file}, config_data={self.config_data})"
