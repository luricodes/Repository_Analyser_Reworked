# repo_analyzer/output/json_output.py

import json
import logging
import os
from typing import Any, Dict, Generator

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

def output_to_json_stream(data_generator: Generator[Dict[str, Any], None, None], output_file: str) -> None:
    """
    Schreibt die Daten in eine JSON-Datei im Streaming-Modus.

    Args:
        data_generator (Generator[Dict[str, Any], None, None]): Ein Generator, der die zu schreibenden Daten liefert.
        output_file (str): Der Pfad zur Ausgabedatei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write('{\n')
            structure = {}
            summary = {}
            for data in data_generator:
                if "summary" in data:
                    summary = data["summary"]
                    continue
                parent = data["parent"]
                filename = data["filename"]
                info = data["info"]

                # Bilde den Pfad in der Struktur
                parts = parent.split(os.sep) if parent else []
                current = structure
                for part in parts:
                    current = current.setdefault(part, {})
                current[filename] = info

            # Füge die Struktur und die Zusammenfassung hinzu
            output = {}
            if summary:
                output["summary"] = summary
            output["structure"] = structure

            json.dump(output, out_file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der JSON-Ausgabedatei im Streaming-Modus: {e}{Style.RESET_ALL}"
        )
