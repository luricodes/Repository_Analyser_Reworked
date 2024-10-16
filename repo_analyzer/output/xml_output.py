# repo_analyzer/output/xml_output.py

from dicttoxml import dicttoxml
import logging
from typing import Dict, Any
from colorama import Fore, Style

def output_to_xml(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine XML-Datei.
    """
    try:
        xml_bytes = dicttoxml(data, custom_root='repository', attr_type=False)
        with open(output_file, 'wb') as xml_file:
            xml_file.write(xml_bytes)
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler beim Konvertieren der Daten zu XML: {e}{Style.RESET_ALL}")