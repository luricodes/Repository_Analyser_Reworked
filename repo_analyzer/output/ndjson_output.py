import json
import logging
from typing import Any, Dict, Generator
import os

from repo_analyzer.utils.time_utils import format_timestamp
from colorama import Fore, Style

def output_to_ndjson(
    data_generator: Generator[Dict[str, Any], None, None],
    output_file: str
) -> None:
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for data in data_generator:
                if not isinstance(data, dict):
                    logging.error(
                        f"Unerwarteter Datentyp: {type(data)}. Erwartet: dict. Daten: {data}"
                    )
                    continue

                if "summary" in data:
                    # Schreiben der Zusammenfassung als separates JSON-Objekt
                    summary_data = data.get("summary")
                    if not isinstance(summary_data, dict):
                        logging.error(
                            f"Unerwarteter Typ für 'summary': {type(summary_data)}. Erwartet: dict."
                        )
                        continue
                    json_line = json.dumps({"summary": summary_data}, ensure_ascii=False)
                    out_file.write(json_line + '\n')
                else:
                    parent = data.get("parent", "")
                    filename = data.get("filename", "")
                    info = data.get("info", {})

                    if not isinstance(info, dict):
                        logging.error(
                            f"Unerwarteter Typ für 'info': {type(info)}. Erwartet: dict. Daten: {info}"
                        )
                        continue

                    file_path = os.path.join(parent, filename) if parent else filename
                    file_path = file_path.replace(os.sep, '/')

                    # Erstellung des JSON-Payloads
                    json_payload = {
                        "path": file_path,
                        "type": info.get("type", ""),
                        "size": info.get("size", ""),
                        "created": format_timestamp(info.get("created")),
                        "modified": format_timestamp(info.get("modified")),
                        "permissions": info.get("permissions", ""),
                        "hash": info.get("file_hash", ""),
                        "content": info.get("content", "")
                    }

                    # Entfernen von leeren Feldern
                    json_payload = {k: v for k, v in json_payload.items() if v}

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
        logging.error(f"IO-Fehler beim Schreiben der NDJSON-Ausgabedatei: {io_err}")
    except Exception as e:
        logging.error(f"Unerwarteter Fehler beim Schreiben der NDJSON-Ausgabedatei: {e}")
