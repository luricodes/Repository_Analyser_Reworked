# repo_analyzer/output/xml_output.py

import logging
from typing import Any, Dict

from colorama import Fore, Style
from dicttoxml import dicttoxml


def output_to_xml(data: Dict[str, Any], output_file: str) -> None:
    """
    Schreibt die Daten in eine XML-Datei.

    Args:
        data (Dict[str, Any]): Die zu konvertierenden Daten.
        output_file (str): Der Pfad zur Ausgabedatei.
    """
    try:
        xml_bytes = dicttoxml(
            data,
            custom_root='repository',
            attr_type=False
        )
        with open(output_file, 'wb') as xml_file:
            xml_file.write(xml_bytes)
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Konvertieren der Daten zu XML: {e}{Style.RESET_ALL}"
        )
