# repo_analyzer/output/yaml_output.py

import logging
from typing import Any, Dict

from colorama import Fore, Style
import yaml

def output_to_yaml(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine YAML-Datei.

    Args:
        data (Dict[str, Any]): Die Daten, die in die YAML-Datei geschrieben werden sollen.
        output_file (str): Der Pfad zur Ausgabedatei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(data, yaml_file, allow_unicode=True, sort_keys=False)
    except (IOError, OSError) as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der YAML-Ausgabedatei: {e}{Style.RESET_ALL}"
        )
