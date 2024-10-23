# repo_analyzer/config/loader.py

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from colorama import Fore, Style

# Constants for supported file extensions
SUPPORTED_EXTENSIONS = {'.yaml', '.yml', '.json'}


def log_error(message: str) -> None:
    """
    Logs an error message in red color.

    Args:
        message (str): The error message.
    """
    logging.error(f"{Fore.RED}{message}{Style.RESET_ALL}")


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Loads a configuration file (YAML or JSON).

    Args:
        config_path (Optional[str]): The path to the configuration file.

    Returns:
        Dict[str, Any]: The loaded configuration as a dictionary.
                        Returns an empty dictionary if no path is provided
                        or an error occurs while loading.
    """
    if not config_path:
        return {}

    config_file = Path(config_path)
    if not config_file.is_file():
        log_error(f"The configuration file does not exist or is not a regular file: {config_path}")
        return {}

    try:
        with config_file.open('r', encoding='utf-8') as file:
            file_suffix = config_file.suffix.lower()
            if file_suffix in ('.yaml', '.yml'):
                config = yaml.safe_load(file) or {}
            elif file_suffix == '.json':
                config = json.load(file)
            else:
                log_error(f"Unknown configuration file format: {config_path}")
                return {}
    except (yaml.YAMLError, json.JSONDecodeError) as parse_err:
        log_error(f"Error parsing the configuration file: {parse_err}")
        return {}
    except IOError as io_err:
        log_error(f"IO error while loading the configuration file: {io_err}")
        return {}
    except Exception as e:
        log_error(f"Unexpected error while loading the configuration file: {e}")
        return {}

    # Validation of configuration parameters
    config = validate_config(config)

    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the loaded configuration parameters.

    Args:
        config (Dict[str, Any]): The loaded configuration dictionary.

    Returns:
        Dict[str, Any]: The validated configuration dictionary.
                        Invalid entries are removed.
    """
    # Validation of the 'max_size' parameter
    max_size = config.get('max_size')
    if max_size is not None:
        if not isinstance(max_size, int) or max_size <= 0:
            log_error(f"Invalid value for 'max_size' in the configuration file: {max_size}")
            config.pop('max_size')  # Remove invalid values

    # Additional validations can be added here
    # Example:
    # log_level = config.get('log_level')
    # if log_level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
    #     log_error(f"Invalid value for 'log_level': {log_level}")
    #     config.pop('log_level')

    return config
