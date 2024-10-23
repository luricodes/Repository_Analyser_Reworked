# repo_analyzer/output/json_output.py

import json
import logging
import os
from typing import Any, Dict, Generator
from repo_analyzer.utils.time_utils import format_timestamp
from colorama import Fore, Style

class JSONStreamWriter:
    """
    Context manager for incrementally writing a JSON file.
    Ensures that the JSON structure is properly closed, even in case of interruptions.
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.file = None
        self.first_entry = True

    def __enter__(self):
        self.file = open(self.output_file, 'w', encoding='utf-8')
        self.file.write('{\n')
        self.file.write('  "structure": [\n')
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
                        f"{Fore.RED}Error closing the JSON structure: {e}{Style.RESET_ALL}"
                    )
            self.file.close()

def output_to_json(data: Dict[str, Any], output_file: str) -> None:
    """
    Writes data in JSON format to a file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(data, out_file, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(
            f"{Fore.RED}Error writing the JSON output file: {e}{Style.RESET_ALL}"
        )

def output_to_json_stream(data_generator: Generator[Dict[str, Any], None, None], output_file: str) -> None:
    """
    Writes the data to a JSON file in streaming mode.

    Args:
        data_generator (Generator[Dict[str, Any], None, None]): A generator that yields the data to be written.
        output_file (str): The path to the output file.
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
            f"{Fore.RED}Error writing the JSON output file in streaming mode: {e}{Style.RESET_ALL}"
        )
