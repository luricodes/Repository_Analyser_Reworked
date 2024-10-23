import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style

def output_to_dot(data: Dict[str, Any], output_file: str) -> None:
    """
    Generates a DOT file based on the repository structure.
    Includes file contents and metadata in the node labels.
    
    :param data: The repository structure and summary.
    :param output_file: Path to the output file in DOT format.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as dot_file:
            dot_file.write("digraph RepositoryStructure {\n")
            dot_file.write('    node [shape=box, style=filled, color="#ADD8E6"];\n')
            dot_file.write("    rankdir=LR;\n")

            def traverse(node: Dict[str, Any], parent_id: str = None):
                for key, value in node.items():
                    # Use the relative path as a unique ID, replace problematic characters
                    unique_id = sanitize_dot_id(str(Path(key).resolve()))
                    node_label = key.replace('"', '\\"')

                    # Initialize label with the name
                    label = f"{node_label}"

                    if isinstance(value, dict):
                        node_type = value.get("type", "directory")
                        if node_type == "directory":
                            # Add metadata for directories if needed
                            dot_file.write(f'    "{unique_id}" [label="{label}", shape=folder, color="#FFA500"];\n')
                            if parent_id:
                                dot_file.write(f'    "{parent_id}" -> "{unique_id}";\n')
                            traverse(value, unique_id)
                        else:
                            # For files, include metadata and content
                            file_info = value
                            size = file_info.get("size", "N/A")
                            created = file_info.get("created", "N/A")
                            modified = file_info.get("modified", "N/A")
                            permissions = file_info.get("permissions", "N/A")
                            file_hash = file_info.get("file_hash", "N/A")
                            content = file_info.get("content", "N/A")

                            # Sanitize and limit the content
                            sanitized_content = sanitize_dot_label(content[:900000])

                            # Construct the label with metadata
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
                        # Handle unexpected data structures
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
        logging.info(f"DOT output successfully written to '{output_file}'.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Error writing the DOT output file: {e}{Style.RESET_ALL}"
        )

def sanitize_dot_id(identifier: str) -> str:
    """
    Sanitizes a string to be used as a DOT node identifier.
    Replaces all non-alphanumeric characters with underscores.
    
    :param identifier: The original identifier.
    :return: A sanitized identifier.
    """
    return ''.join([c if c.isalnum() else '_' for c in identifier])

def sanitize_dot_label(label: str) -> str:
    """
    Sanitizes a string to be used within DOT labels.
    Replaces quotation marks and line breaks.
    
    :param label: The original label text.
    :return: A sanitized label.
    """
    return label.replace('"', '\\"').replace('\n', '\\n')
