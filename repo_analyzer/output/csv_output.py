# repo_analyzer/output/csv_output.py

import csv
import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style

def output_to_csv(data: Dict[str, Any], output_file: str) -> None:
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Path', 'Type', 'Size', 'Created', 'Modified', 'Permissions', 'Hash'])

            def traverse(node: Dict[str, Any], parent: str = ""):
                for key, value in node.items():
                    current_path = f"{parent}/{key}" if parent else key
                    if isinstance(value, dict):
                        file_type = value.get("type", "directory")
                        size = value.get("size", "")
                        created = value.get("created", "")
                        modified = value.get("modified", "")
                        permissions = value.get("permissions", "")
                        file_hash = value.get("file_hash", "")
                        writer.writerow([current_path, file_type, size, created, modified, permissions, file_hash])
                        traverse(value, current_path)
                    else:
                        writer.writerow([current_path, "unknown", "", "", "", "", ""])

            structure = data.get("structure", {})
            traverse(structure)

            summary = data.get("summary", {})
            if summary:
                writer.writerow([])
                writer.writerow(['Summary'])
                for key, value in summary.items():
                    writer.writerow([key, value])

        logging.info(f"CSV-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der CSV-Ausgabedatei: {e}{Style.RESET_ALL}"
        )
