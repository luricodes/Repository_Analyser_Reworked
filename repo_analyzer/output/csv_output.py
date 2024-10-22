import csv
import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style
from datetime import datetime

# Maximale Länge der Content-Spalte (optional)
MAX_CONTENT_LENGTH = 900000

def truncate_content(content: str) -> str:
    if len(content) > MAX_CONTENT_LENGTH:
        return content[:MAX_CONTENT_LENGTH] + '... [Inhalt gekürzt]'
    return content

def output_to_csv(data: Dict[str, Any], output_file: str) -> None:
    logging.debug("Starte CSV-Ausgabefunktion.")
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
            # Hinzufügen der 'Content'-Spalte und Verwendung von QUOTE_ALL zur Vermeidung von Escaping-Problemen
            fieldnames = ['Path', 'Type', 'Size', 'Created', 'Modified', 'Permissions', 'Hash', 'Content']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            def traverse(node: Dict[str, Any], parent: str = ""):
                for key, value in node.items():
                    current_path = f"{parent}/{key}" if parent else key
                    if isinstance(value, dict):
                        node_type = value.get("type", "directory")
                        if node_type == "directory":
                            writer.writerow({
                                'Path': current_path,
                                'Type': node_type,
                                'Size': '',
                                'Created': '',
                                'Modified': '',
                                'Permissions': '',
                                'Hash': '',
                                'Content': ''
                            })
                            logging.debug(f"Schreibe Ordner: {current_path}")
                            traverse(value, current_path)
                        else:
                            size = value.get("size", "")
                            created = format_timestamp(value.get("created", ""))
                            modified = format_timestamp(value.get("modified", ""))
                            permissions = value.get("permissions", "")
                            file_hash = value.get("file_hash", "")
                            content = value.get("content", "")
                            
                            # Inhalt ggf. kürzen
                            content = truncate_content(content)
                            
                            writer.writerow({
                                'Path': current_path,
                                'Type': node_type,
                                'Size': size,
                                'Created': created,
                                'Modified': modified,
                                'Permissions': permissions,
                                'Hash': file_hash,
                                'Content': content
                            })
                            logging.debug(f"Schreibe Datei: {current_path}")
                    else:
                        writer.writerow({
                            'Path': current_path,
                            'Type': "unknown",
                            'Size': '',
                            'Created': '',
                            'Modified': '',
                            'Permissions': '',
                            'Hash': '',
                            'Content': ''
                        })
                        logging.debug(f"Schreibe unbekannten Typ: {current_path}")

            def format_timestamp(timestamp: Any) -> str:
                if isinstance(timestamp, (int, float)):
                    try:
                        return datetime.fromtimestamp(timestamp).isoformat()
                    except (OSError, OverflowError, ValueError):
                        logging.warning(f"Ungültiger Timestamp: {timestamp}")
                        return ""
                return ""

            structure = data.get("structure", data)
            logging.debug(f"Datenstruktur vor Traversierung: {structure}")

            traverse(structure)

            summary = data.get("summary")
            if summary:
                # Leere Zeile für bessere Lesbarkeit
                writer.writerow({})
                # Kopfzeile für die Zusammenfassung
                writer.writerow({
                    'Path': 'Summary',
                    'Type': '',
                    'Size': '',
                    'Created': '',
                    'Modified': '',
                    'Permissions': '',
                    'Hash': '',
                    'Content': ''
                })
                logging.debug("Schreibe Summary.")
                for key, value in summary.items():
                    # Optional: Kürze Zusammenfassungswerte, falls zu lang
                    value = truncate_content(str(value))
                    writer.writerow({
                        'Path': key,
                        'Type': '',
                        'Size': '',
                        'Created': '',
                        'Modified': '',
                        'Permissions': '',
                        'Hash': '',
                        'Content': value
                    })

        logging.info(f"CSV-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except IOError as e:
        logging.error(f"IO-Fehler beim Schreiben der CSV-Ausgabedatei: {e}")
    except csv.Error as e:
        logging.error(f"CSV-Fehler: {e}")
    except Exception as e:
        logging.error(f"Unerwarteter Fehler beim Schreiben der CSV-Ausgabedatei: {e}")
