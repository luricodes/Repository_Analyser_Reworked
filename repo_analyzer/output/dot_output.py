import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style

def output_to_dot(data: Dict[str, Any], output_file: str) -> None:
    """
    Generiert eine DOT-Datei basierend auf der Repository-Struktur.
    Inkludiert Dateiinhalte und Metadaten in den Knotenlabels.
    
    :param data: Die Repository-Struktur und Zusammenfassung.
    :param output_file: Pfad zur Ausgabedatei im DOT-Format.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as dot_file:
            dot_file.write("digraph RepositoryStructure {\n")
            dot_file.write('    node [shape=box, style=filled, color="#ADD8E6"];\n')
            dot_file.write("    rankdir=LR;\n")

            def traverse(node: Dict[str, Any], parent_id: str = None):
                for key, value in node.items():
                    # Verwende den relativen Pfad als eindeutige ID, ersetze problematische Zeichen
                    unique_id = sanitize_dot_id(str(Path(key).resolve()))
                    node_label = key.replace('"', '\\"')

                    # Initialize label with the name
                    label = f"{node_label}"

                    if isinstance(value, dict):
                        node_type = value.get("type", "directory")
                        if node_type == "directory":
                            # Füge Metadaten für Verzeichnisse hinzu, falls benötigt
                            dot_file.write(f'    "{unique_id}" [label="{label}", shape=folder, color="#FFA500"];\n')
                            if parent_id:
                                dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')
                            traverse(value, unique_id)
                        else:
                            # Für Dateien Metadaten und Inhalt einbeziehen
                            file_info = value
                            size = file_info.get("size", "N/A")
                            created = file_info.get("created", "N/A")
                            modified = file_info.get("modified", "N/A")
                            permissions = file_info.get("permissions", "N/A")
                            file_hash = file_info.get("file_hash", "N/A")
                            content = file_info.get("content", "N/A")

                            # Sanitisiere und begrenze den Inhalt
                            sanitized_content = sanitize_dot_label(content[:900000])

                            # Konstruiere das Label mit Metadaten
                            label += (
                                f"\\nSize: {size} bytes"
                                f"\\nCreated: {created}"
                                f"\\nModified: {modified}"
                                f"\\nPermissions: {permissions}"
                                f"\\nHash: {file_hash}"
                                #f"\\nContent: {sanitized_content}"
                            )

                            dot_file.write(f'    "{unique_id}" [label="{label}", shape=note, color="#90EE90"];\n')
                            if parent_id:
                                dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')
                    else:
                        # Behandlung unerwarteter Datenstrukturen
                        dot_file.write(f'    "{unique_id}" [label="{key}", shape=note, color="#90EE90"];\n')
                        if parent_id:
                            dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')

            structure = data.get("structure", data)

            traverse(structure)

            summary = data.get("summary")
            if summary:
                summary_id = sanitize_dot_id("summary")
                dot_file.write("\n    subgraph cluster_summary {\n")
                dot_file.write('        label="Summary";\n')
                dot_file.write("        color=lightgrey;\n")
                for key, value in summary.items():
                    sanitized_key = key.replace('"', '\\"')
                    summary_node_id = f"{summary_id}_{sanitize_dot_id(key)}"
                    dot_file.write(f'        "{summary_node_id}" [label="{sanitized_key}: {value}", shape=note, color="#D3D3D3"];\n')
                dot_file.write("    }\n")
            dot_file.write("}\n")
        logging.info(f"DOT-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der DOT-Ausgabedatei: {e}{Style.RESET_ALL}"
        )

def sanitize_dot_id(identifier: str) -> str:
    """
    Sanitizes a string to be used as a DOT node identifier.
    Ersetzt alle nicht-alphanumerischen Zeichen durch Unterstriche.
    
    :param identifier: Der ursprüngliche Identifier.
    :return: Ein sanitisiertes Identifier.
    """
    return ''.join([c if c.isalnum() else '_' for c in identifier])

def sanitize_dot_label(label: str) -> str:
    """
    Sanitizes a string to be used within DOT labels.
    Ersetzt Anführungszeichen und Zeilenumbrüche.
    
    :param label: Der ursprüngliche Label-Text.
    :return: Ein sanitisiertes Label.
    """
    return label.replace('"', '\\"').replace('\n', '\\n')
