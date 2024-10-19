# repo_analyzer/output/xml_output.py

import logging
import re
from typing import Any, Dict
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

from colorama import Fore, Style

def sanitize_tag(tag: str) -> str:
    """
    Sanitizes a string to be used as an XML tag.

    Args:
        tag (str): The original tag string.

    Returns:
        str: A sanitized tag string suitable for XML.
    """
    # Replace spaces and invalid characters with underscores
    tag = re.sub(r'\s+', '_', tag)
    tag = re.sub(r'[^\w\-\.]', '', tag)
    # Ensure the tag doesn't start with a number
    if re.match(r'^\d', tag):
        tag = f'item_{tag}'
    return tag

def dict_to_xml(parent: Element, data: Any) -> None:
    """
    Recursively converts a dictionary to XML elements.

    Args:
        parent (Element): The parent XML element.
        data (Any): The data to convert.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            tag = sanitize_tag(str(key))
            sub_element = SubElement(parent, tag)
            dict_to_xml(sub_element, value)
    elif isinstance(data, list):
        for item in data:
            # Use a generic tag for list items or derive from context
            item_tag = 'item'
            sub_element = SubElement(parent, item_tag)
            dict_to_xml(sub_element, item)
    else:
        parent.text = str(data)

def prettify_xml(element: Element) -> str:
    """
    Returns a pretty-printed XML string for the Element.

    Args:
        element (Element): The XML element.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = tostring(element, 'utf-8')
    try:
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler beim Formatieren der XML: {e}{Style.RESET_ALL}")
        return rough_string.decode('utf-8')

def output_to_xml(data: Dict[str, Any], output_file: str) -> None:
    """
    Writes the data to an XML file with improved structure and readability.

    Args:
        data (Dict[str, Any]): The data to convert to XML.
        output_file (str): The path to the output XML file.
    """
    try:
        root = Element('repository')
        dict_to_xml(root, data)

        pretty_xml = prettify_xml(root)

        with open(output_file, 'w', encoding='utf-8') as xml_file:
            xml_file.write(pretty_xml)
        
        logging.info(f"XML-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Fehler beim Konvertieren der Daten zu XML: {e}{Style.RESET_ALL}"
        )
