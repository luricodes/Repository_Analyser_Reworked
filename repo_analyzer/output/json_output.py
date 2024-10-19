# repo_analyzer/output/json_output.py

import json
import logging
import os
from typing import Any, Dict, Generator

from colorama import Fore, Style

class JSONStreamWriter:
    """
    Kontextmanager für das inkrementelle Schreiben einer JSON-Datei.
    Sichert, dass die JSON-Struktur korrekt abgeschlossen wird, auch bei Unterbrechungen.
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.file = None
        self.first_entry = True

    def __enter__(self):
        self.file = open(self.output_file, 'w', encoding='utf-8')
        self.file.write('{\n')
        self.file.write('  "structure": [\n')  # Changed to list for streaming
        return self

    def write_entry(self, data: Dict[str, Any]) -> None:
        if not self.first_entry:
            self.file.write(',\n')
        else:
            self.first_entry = False
        json.dump(data, self.file, ensure_ascii=False, indent=4)

    def write_summary(self, summary: Dict[str, Any]) -> None:
        self.file.write('\n  ],\n')
        self.file.write('  "summary": ')
        json.dump(summary, self.file, ensure_ascii=False, indent=4)
        self.file.write('\n')
        self.file.write('}\n')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            if exc_type is not None:
                # If an exception occurred, close the JSON structure gracefully
                try:
                    self.file.write('\n  ],\n')
                    self.file.write('  "summary": {}\n')
                    self.file.write('}\n')
                except Exception as e:
                    logging.error(
                        f"{Fore.RED}Fehler beim Abschließen der JSON-Struktur: {e}{Style.RESET_ALL}"
                    )
            self.file.close()

def output_to_json(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine JSON-Datei im Standardmodus.

    Args:
        data (Dict[str, Any]): Die Daten, die in die JSON-Datei geschrieben werden sollen.
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
        with JSONStreamWriter(output_file) as writer:
            summary = {}
            for data in data_generator:
                if "summary" in data:
                    summary = data["summary"]
                    continue
                parent = data["parent"]
                filename = data["filename"]
                info = data["info"]

                # Prepare the JSON entry
                file_path = os.path.join(parent, filename) if parent else filename
                file_entry = {
                    "path": file_path.replace(os.sep, '/'),
                    "info": info
                }

                writer.write_entry(file_entry)

            # Write the summary at the end
            if summary:
                writer.write_summary(summary)
            else:
                writer.write_summary({})
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der JSON-Ausgabedatei im Streaming-Modus: {e}{Style.RESET_ALL}"
        )
