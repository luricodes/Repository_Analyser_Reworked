# repo_analyzer/output/ndjson_output.py

import json
import logging
from typing import Any, Dict, Generator

from colorama import Fore, Style

def output_to_ndjson(data_generator: Generator[Dict[str, Any], None, None], output_file: str) -> None:
    """
    Schreibt die Daten in eine NDJSON-Datei (Newline Delimited JSON).

    Args:
        data_generator (Generator[Dict[str, Any], None, None]): Ein Generator, der die zu schreibenden Daten liefert.
        output_file (str): Der Pfad zur Ausgabedatei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for data in data_generator:
                json_line = json.dumps(data, ensure_ascii=False)
                out_file.write(json_line + '\n')
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der NDJSON-Ausgabedatei: {e}{Style.RESET_ALL}"
        )
