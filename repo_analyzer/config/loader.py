# repo_analyzer/config/loader.py

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from colorama import Fore, Style

# Konstanten für unterstützte Dateiendungen
SUPPORTED_EXTENSIONS = {'.yaml', '.yml', '.json'}


def log_error(message: str) -> None:
    """
    Protokolliert eine Fehlermeldung in roter Farbe.

    Args:
        message (str): Die Fehlermeldung.
    """
    logging.error(f"{Fore.RED}{message}{Style.RESET_ALL}")


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Lädt eine Konfigurationsdatei (YAML oder JSON).

    Args:
        config_path (Optional[str]): Der Pfad zur Konfigurationsdatei.

    Returns:
        Dict[str, Any]: Die geladene Konfiguration als Dictionary.
                        Gibt ein leeres Dictionary zurück, wenn kein Pfad angegeben ist
                        oder ein Fehler beim Laden auftritt.
    """
    if not config_path:
        return {}

    config_file = Path(config_path)
    if not config_file.is_file():
        log_error(f"Die Konfigurationsdatei existiert nicht oder ist kein reguläres Datei: {config_path}")
        return {}

    try:
        with config_file.open('r', encoding='utf-8') as file:
            file_suffix = config_file.suffix.lower()
            if file_suffix in ('.yaml', '.yml'):
                config = yaml.safe_load(file) or {}
            elif file_suffix == '.json':
                config = json.load(file)
            else:
                log_error(f"Unbekanntes Konfigurationsdateiformat: {config_path}")
                return {}
    except (yaml.YAMLError, json.JSONDecodeError) as parse_err:
        log_error(f"Fehler beim Parsen der Konfigurationsdatei: {parse_err}")
        return {}
    except IOError as io_err:
        log_error(f"IO-Fehler beim Laden der Konfigurationsdatei: {io_err}")
        return {}
    except Exception as e:
        log_error(f"Unerwarteter Fehler beim Laden der Konfigurationsdatei: {e}")
        return {}

    # Validierung der Konfigurationsparameter
    config = validate_config(config)

    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validiert die geladenen Konfigurationsparameter.

    Args:
        config (Dict[str, Any]): Das geladene Konfigurations-Dictionary.

    Returns:
        Dict[str, Any]: Das validierte Konfigurations-Dictionary.
                        Ungültige Einträge werden entfernt.
    """
    # Validierung des 'max_size' Parameters
    max_size = config.get('max_size')
    if max_size is not None:
        if not isinstance(max_size, int) or max_size <= 0:
            log_error(f"Ungültiger Wert für 'max_size' in der Konfigurationsdatei: {max_size}")
            config.pop('max_size')  # Entfernen ungültiger Werte

    # Weitere Validierungen können hier hinzugefügt werden
    # Beispiel:
    # log_level = config.get('log_level')
    # if log_level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
    #     log_error(f"Ungültiger Wert für 'log_level': {log_level}")
    #     config.pop('log_level')

    return config
