# repo_analyzer/output/yaml_output.py

import yaml
import logging
from colorama import Fore, Style
from typing import Dict, Any

def output_to_yaml(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine YAML-Datei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(data, yaml_file, allow_unicode=True, sort_keys=False)
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler beim Schreiben der YAML-Ausgabedatei: {e}{Style.RESET_ALL}")