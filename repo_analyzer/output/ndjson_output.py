import json
import logging
from typing import Any, Dict, Generator
import os

from repo_analyzer.utils.time_utils import format_timestamp
from colorama import Fore, Style

def output_to_ndjson(data_generator: Generator[Dict[str, Any], None, None], output_file: str) -> None:
    """
    Schreibt die Daten aus dem Generator in eine NDJSON-Datei.
    
    Jeder Eintrag im Generator muss ein Dictionary sein. 
    Wenn ein Dictionary den Schlüssel 'summary' enthält, wird es separat geschrieben.
    Andernfalls wird der Eintrag als Datei in der Repository-Struktur dargestellt.
    
    :param data_generator: Generator, der die Daten liefert.
    :param output_file: Pfad zur Ausgabedatei.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for data in data_generator:
                # Typüberprüfung des Datenobjekts
                if not isinstance(data, dict):
                    logging.error(f"Unerwarteter Datentyp: {type(data)}. Erwartet: dict. Daten: {data}")
                    continue

                if "summary" in data:
                    summary_data = data.get("summary")
                    if not isinstance(summary_data, dict):
                        logging.error(f"Unerwarteter Typ für 'summary': {type(summary_data)}. Erwartet: dict.")
                        continue
                    json_line = json.dumps({"summary": summary_data}, ensure_ascii=False)
                    out_file.write(json_line + '\n')
                else:
                    parent = data.get("parent", "")
                    filename = data.get("filename", "")
                    info = data.get("info", {})

                    # Typüberprüfung des 'info' Objekts
                    if not isinstance(info, dict):
                        logging.error(f"Unerwarteter Typ für 'info': {type(info)}. Erwartet: dict. Daten: {info}")
                        continue

                    file_path = os.path.join(parent, filename) if parent else filename
                    file_path = file_path.replace(os.sep, '/')
                    json_payload = {
                        "path": file_path,
                        "type": info.get("type", ""),
                        "size": info.get("size", ""),
                        "created": format_timestamp(info.get("created", "")),
                        "modified": format_timestamp(info.get("modified", "")),
                        "permissions": info.get("permissions", ""),
                        "hash": info.get("file_hash", ""),
                        "content": info.get("content", "")                      
                    }

                    # Überprüfung, ob alle benötigten Felder vorhanden sind
                    required_fields = ["path", "type", "size", "created", "modified", "permissions", "hash", "content"]
                    missing_fields = [field for field in required_fields if field not in json_payload]
                    if missing_fields:
                        logging.error(f"Fehlende Felder in 'json_payload': {missing_fields}. Daten: {json_payload}")
                        continue

                    try:
                        json_line = json.dumps(json_payload, ensure_ascii=False)
                        out_file.write(json_line + '\n')
                        logging.debug(f"Schreibe Eintrag für Datei: {file_path}")
                    except (TypeError, ValueError) as json_err:
                        logging.error(
                            f"Fehler beim Serialisieren der JSON-Daten für '{file_path}': {json_err}"
                        )
        logging.info(f"NDJSON-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except IOError as io_err:
        logging.error(
            f"IO-Fehler beim Schreiben der NDJSON-Ausgabedatei: {io_err}"
        )
    except Exception as e:
        logging.error(
            f"Unerwarteter Fehler beim Schreiben der NDJSON-Ausgabedatei: {e}"
        )
