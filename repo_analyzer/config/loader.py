# repo_analyzer/config/loader.py

import json
import yaml
import logging
from colorama import Fore, Style
from typing import Optional, Dict, Any

def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Lädt eine Konfigurationsdatei (YAML oder JSON).
    """
    if not config_path:
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            if config_path.lower().endswith(('.yaml', '.yml')):
                return yaml.safe_load(file) or {}
            elif config_path.lower().endswith('.json'):
                return json.load(file)
            else:
                logging.error(f"{Fore.RED}Unbekanntes Konfigurationsdateiformat: {config_path}{Style.RESET_ALL}")
                return {}
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler beim Laden der Konfigurationsdatei: {e}{Style.RESET_ALL}")
        return {}