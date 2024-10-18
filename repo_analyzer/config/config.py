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
    Hilfsfunktion zum Loggen von Fehlern mit roten Farben.

    Args:
        message (str): Die Fehlermeldung.
    """
    logging.error(f"{Fore.RED}{message}{Style.RESET_ALL}")


class Config:
    """
    Singleton-Klasse zur Verwaltung der Konfiguration.
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
        Initialisiert die Konfigurationsdaten, falls noch nicht geschehen.
        """
        if not hasattr(self, 'data'):
            self.data = {}

    def load(self, config_path: Optional[str]) -> None:
        """
        Lädt die Konfigurationsdatei, falls angegeben.

        Args:
            config_path (Optional[str]): Der Pfad zur Konfigurationsdatei.
        """
        if config_path:
            try:
                loaded_config = load_config(config_path)
                if isinstance(loaded_config, dict):
                    self.data.update(loaded_config)
                else:
                    raise TypeError("Geladene Konfiguration muss ein Wörterbuch sein.")
            except Exception as e:
                log_error(f"Fehler beim Laden der Konfigurationsdatei: {e}")

    def get_max_size(self, cli_max_size: Optional[int]) -> int:
        """
        Bestimmt die maximale Dateigröße basierend auf CLI-Argumenten, Konfiguration und Standardwerten.

        Args:
            cli_max_size (Optional[int]): Der vom Benutzer angegebene Wert für max_size in MB.

        Returns:
            int: Die zu verwendende maximale Dateigröße in Bytes.

        Raises:
            ValueError: Wenn der angegebene Wert ungültig ist.
        """
        if cli_max_size is not None:
            if cli_max_size <= 0:
                raise ValueError("Die maximale Dateigröße muss positiv sein.")
            return cli_max_size * 1024 * 1024  # Umwandlung von MB in Bytes

        config_max_size = self.data.get('max_size')
        if config_max_size is not None:
            if isinstance(config_max_size, int) and config_max_size > 0:
                return config_max_size * 1024 * 1024  # Umwandlung von MB in Bytes
            else:
                raise ValueError(
                    "Der Wert für 'max_size' in der Konfigurationsdatei ist ungültig. "
                    "Bitte geben Sie einen positiven ganzzahligen Wert in MB an."
                )

        return DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024  # Standardwert in Bytes

    def save(self, config_path: str) -> None:
        """
        Speichert die aktuelle Konfiguration in eine Datei (YAML oder JSON).

        Args:
            config_path (str): Der Pfad zur Konfigurationsdatei.
        """
        config_file = Path(config_path)
        suffix = config_file.suffix.lower()

        if suffix not in SUPPORTED_FORMATS:
            log_error(f"Unbekanntes Konfigurationsdateiformat zum Speichern: {config_path}")
            return

        try:
            with config_file.open('w', encoding='utf-8') as file:
                if suffix in ('.yaml', '.yml'):
                    yaml.dump(self.data, file, allow_unicode=True, sort_keys=False)
                elif suffix == '.json':
                    json.dump(self.data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            log_error(f"Fehler beim Speichern der Konfigurationsdatei: {e}")
