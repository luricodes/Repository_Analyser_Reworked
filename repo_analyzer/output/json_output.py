# repo_analyzer/output/json_output.py

import json
import logging
from typing import Any, Dict

from colorama import Fore, Style

def output_to_json(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine JSON-Datei.

    Args:
        data (Dict[str, Any]): Die zu konvertierenden Daten.
        output_file (str): Der Pfad zur Ausgabedatei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(data, out_file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der JSON-Ausgabedatei: {e}{Style.RESET_ALL}"
        )
