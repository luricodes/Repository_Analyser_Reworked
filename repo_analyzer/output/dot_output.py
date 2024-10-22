# repo_analyzer/output/dot_output.py

import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style
import uuid

def output_to_dot(data: Dict[str, Any], output_file: str) -> None:
    try:
        with open(output_file, 'w', encoding='utf-8') as dot_file:
            dot_file.write("digraph RepositoryStructure {\n")
            dot_file.write("    node [shape=box, style=filled, color=\"#ADD8E6\"];\n")
            dot_file.write("    rankdir=LR;\n")  # Left to Right layout

            node_ids = {}
            def traverse(node: Dict[str, Any], parent_id: str = None):
                for key, value in node.items():
                    unique_id = str(uuid.uuid4())
                    node_label = key.replace('"', '\\"')  # Escape quotes
                    if isinstance(value, dict) and value.get("type") == "directory":
                        dot_file.write(f'    "{unique_id}" [label="{node_label}", shape=folder, color="#FFA500"];\n')
                        if parent_id:
                            dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')
                        traverse(value, unique_id)
                    else:
                        dot_file.write(f'    "{unique_id}" [label="{node_label}", shape=note, color="#90EE90"];\n')
                        if parent_id:
                            dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')

            structure = data.get("structure", {})
            traverse(structure)

            summary = data.get("summary", {})
            if summary:
                summary_id = str(uuid.uuid4())
                dot_file.write("\n    subgraph cluster_summary {\n")
                dot_file.write("        label=\"Summary\";\n")
                dot_file.write("        color=lightgrey;\n")
                for key, value in summary.items():
                    sanitized_key = key.replace('"', '\\"')
                    dot_file.write(f'        "{summary_id}_{sanitized_key}" [label="{sanitized_key}: {value}", shape=note, color="#D3D3D3"];\n')
                dot_file.write("    }\n")
            dot_file.write("}\n")
        logging.info(f"DOT-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der DOT-Ausgabedatei: {e}{Style.RESET_ALL}"
        )
