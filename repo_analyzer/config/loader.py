# repo_analyzer/config/loader.py

from typing import Optional, Dict, Any
from pathlib import Path
import json
import yaml
import logging
from colorama import Fore, Style

def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Lädt eine Konfigurationsdatei (YAML oder JSON).

    Args:
        config_path (Optional[str]): Der Pfad zur Konfigurationsdatei.

    Returns:
        Dict[str, Any]: Die geladene Konfiguration als Dictionary.
    """
    if not config_path:
        return {}

    config_file = Path(config_path)
    if not config_file.exists():
        logging.error(
            f"{Fore.RED}Die Konfigurationsdatei existiert nicht: {config_path}{Style.RESET_ALL}"
        )
        return {}

    try:
        with config_file.open('r', encoding='utf-8') as file:
            file_suffix = config_file.suffix.lower()
            if file_suffix in ('.yaml', '.yml'):
                config = yaml.safe_load(file) or {}
            elif file_suffix == '.json':
                config = json.load(file)
            else:
                logging.error(
                    f"{Fore.RED}Unbekanntes Konfigurationsdateiformat: {config_path}{Style.RESET_ALL}"
                )
                return {}
    except (yaml.YAMLError, json.JSONDecodeError) as parse_err:
        logging.error(
            f"{Fore.RED}Fehler beim Parsen der Konfigurationsdatei: {parse_err}{Style.RESET_ALL}"
        )
        return {}
    except IOError as io_err:
        logging.error(
            f"{Fore.RED}IO-Fehler beim Laden der Konfigurationsdatei: {io_err}{Style.RESET_ALL}"
        )
        return {}
    except Exception as e:
        logging.error(
            f"{Fore.RED}Unerwarteter Fehler beim Laden der Konfigurationsdatei: {e}{Style.RESET_ALL}"
        )
        return {}

    # Validierung des max_size Parameters
    max_size = config.get('max_size')
    if max_size is not None:
        if not isinstance(max_size, int) or max_size <= 0:
            logging.error(
                f"{Fore.RED}Ungültiger Wert für 'max_size' in der Konfigurationsdatei: {max_size}{Style.RESET_ALL}"
            )
            config.pop('max_size')  # Entfernen ungültiger Werte

    return config
