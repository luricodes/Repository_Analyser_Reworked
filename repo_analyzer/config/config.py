# repo_analyzer/config/config.py

from typing import Optional, Dict, Any
from .defaults import DEFAULT_MAX_FILE_SIZE
from .loader import load_config
import logging
from colorama import Fore, Style
import json
import yaml
from pathlib import Path

class Config:
    """
    Singleton-Klasse zur Verwaltung der Konfiguration.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.data = {}
        return cls._instance

    def load(self, config_path: Optional[str]) -> None:
        """
        Lädt die Konfigurationsdatei, falls angegeben.

        Args:
            config_path (Optional[str]): Der Pfad zur Konfigurationsdatei.
        """
        if config_path:
            loaded_config = load_config(config_path)
            self.data.update(loaded_config)

    def get_max_size(self, cli_max_size: Optional[int]) -> int:
        """
        Bestimmt die maximale Dateigröße basierend auf CLI-Argumenten, Konfiguration und Standardwerten.

        Args:
            cli_max_size (Optional[int]): Der vom Benutzer angegebene Wert für max_size in Bytes.

        Returns:
            int: Die zu verwendende maximale Dateigröße in Bytes.

        Raises:
            ValueError: Wenn der angegebene Wert ungültig ist.
        """
        if cli_max_size is not None:
            if cli_max_size <= 0:
                raise ValueError("Die maximale Dateigröße muss positiv sein.")
            return cli_max_size
        elif 'max_size' in self.data:
            config_max_size = self.data['max_size']
            if isinstance(config_max_size, int) and config_max_size > 0:
                return config_max_size
            else:
                raise ValueError("Der Wert für 'max_size' in der Konfigurationsdatei ist ungültig.")
        else:
            return DEFAULT_MAX_FILE_SIZE

    def save(self, config_path: str) -> None:
        """
        Speichert die aktuelle Konfiguration in eine Datei (YAML oder JSON).

        Args:
            config_path (str): Der Pfad zur Konfigurationsdatei.
        """
        config_file = Path(config_path)
        try:
            with config_file.open('w', encoding='utf-8') as file:
                if config_file.suffix.lower() in ('.yaml', '.yml'):
                    yaml.dump(self.data, file, allow_unicode=True, sort_keys=False)
                elif config_file.suffix.lower() == '.json':
                    json.dump(self.data, file, ensure_ascii=False, indent=4)
                else:
                    logging.error(
                        f"{Fore.RED}Unbekanntes Konfigurationsdateiformat zum Speichern: {config_path}{Style.RESET_ALL}"
                    )
        except Exception as e:
            logging.error(
                f"{Fore.RED}Fehler beim Speichern der Konfigurationsdatei: {e}{Style.RESET_ALL}"
            )
