import csv
import logging
from typing import Dict, Any
from pathlib import Path
from colorama import Fore, Style
from datetime import datetime

# Maximum length of the content column (optional)
MAX_CONTENT_LENGTH = 900000

def truncate_content(content: str) -> str:
    if len(content) > MAX_CONTENT_LENGTH:
        return content[:MAX_CONTENT_LENGTH] + '... [Content truncated]'
    return content

def output_to_csv(data: Dict[str, Any], output_file: str) -> None:
    logging.debug("Starting CSV output function.")
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
            # Add the 'Content' column and use QUOTE_ALL to avoid escaping issues
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
                            logging.debug(f"Writing folder: {current_path}")
                            traverse(value, current_path)
                        else:
                            size = value.get("size", "")
                            created = format_timestamp(value.get("created", ""))
                            modified = format_timestamp(value.get("modified", ""))
                            permissions = value.get("permissions", "")
                            file_hash = value.get("file_hash", "")
                            content = value.get("content", "")
                            
                            # Truncate content if necessary
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
                            logging.debug(f"Writing file: {current_path}")
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
                        logging.debug(f"Writing unknown type: {current_path}")

            def format_timestamp(timestamp: Any) -> str:
                if isinstance(timestamp, (int, float)):
                    try:
                        return datetime.fromtimestamp(timestamp).isoformat()
                    except (OSError, OverflowError, ValueError):
                        logging.warning(f"Invalid timestamp: {timestamp}")
                        return ""
                return ""

            structure = data.get("structure", data)
            logging.debug(f"Data structure before traversal: {structure}")

            traverse(structure)

            summary = data.get("summary")
            if summary:
                # Empty line for better readability
                writer.writerow({})
                # Header row for the summary
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
                logging.debug("Writing summary.")
                for key, value in summary.items():
                    # Optional: Truncate summary values if too long
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

        logging.info(f"CSV output successfully written to '{output_file}'.")
    except IOError as e:
        logging.error(f"IO error while writing the CSV output file: {e}")
    except csv.Error as e:
        logging.error(f"CSV error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while writing the CSV output file: {e}")
