# repo_analyzer/config/config.py

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Literal

import yaml
from colorama import Fore, Style

from .defaults import (
    CACHE_DB_FILE,
    DEFAULT_EXCLUDED_FILES,
    DEFAULT_EXCLUDED_FOLDERS,
    DEFAULT_MAX_FILE_SIZE_MB
)
from .loader import load_config


# Konstanten für unterstützte Dateiformate
SUPPORTED_FORMATS: tuple[Literal['.yaml', '.yml', '.json'], ...] = (
    '.yaml',
    '.yml',
    '.json',
)


def log_error(message: str) -> None:
    """
    Helper function to log errors with red colors.

    Args:
        message (str): The error message.
    """
    logging.error(f"{Fore.RED}{message}{Style.RESET_ALL}")


class Config:
    """
    Singleton class for managing configuration.
    """

    _instance: Optional['Config'] = None
    _lock: threading.Lock = threading.Lock()

    data: Dict[str, Any]

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initializes the configuration data if not already done.
        """
        if not hasattr(self, 'data'):
            self.data = {}

    def load(self, config_path: Optional[str]) -> None:
        """
        Loads the configuration file if provided.

        Args:
            config_path (Optional[str]): The path to the configuration file.
        """
        if config_path:
            try:
                loaded_config = load_config(config_path)
                if isinstance(loaded_config, dict):
                    self.data.update(loaded_config)
                else:
                    raise TypeError("Loaded configuration must be a dictionary.")
            except Exception as e:
                log_error(f"Error loading configuration file: {e}")

    def get_max_size(self, cli_max_size: Optional[int]) -> int:
        """
        Determines the maximum file size based on CLI arguments, configuration, and default values.

        Args:
            cli_max_size (Optional[int]): The user-specified value for max_size in MB.

        Returns:
            int: The maximum file size to use in bytes.

        Raises:
            ValueError: If the provided value is invalid.
        """
        if cli_max_size is not None:
            if cli_max_size <= 0:
                raise ValueError("The maximum file size must be positive.")
            return cli_max_size * 1024 * 1024  # Convert from MB to bytes

        config_max_size = self.data.get('max_size')
        if config_max_size is not None:
            if isinstance(config_max_size, int) and config_max_size > 0:
                return config_max_size * 1024 * 1024  # Convert from MB to bytes
            else:
                raise ValueError(
                    "The value for 'max_size' in the configuration file is invalid. "
                    "Please provide a positive integer value in MB."
                )

        return DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024  # Default value in bytes

    def save(self, config_path: str) -> None:
        """
        Saves the current configuration to a file (YAML or JSON).

        Args:
            config_path (str): The path to the configuration file.
        """
        config_file = Path(config_path)
        suffix = config_file.suffix.lower()

        if suffix not in SUPPORTED_FORMATS:
            log_error(f"Unknown configuration file format for saving: {config_path}")
            return

        try:
            with config_file.open('w', encoding='utf-8') as file:
                if suffix in ('.yaml', '.yml'):
                    yaml.dump(self.data, file, allow_unicode=True, sort_keys=False)
                elif suffix == '.json':
                    json.dump(self.data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            log_error(f"Error saving configuration file: {e}")
