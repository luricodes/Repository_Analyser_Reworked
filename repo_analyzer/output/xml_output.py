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
    Recursively converts a dictionary to XML elements, distinguishing between directories and files.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) and 'type' in value:
                # File
                file_element = SubElement(parent, 'file', name=key)
                for file_key, file_value in value.items():
                    if file_key != 'name' and file_key != 'type':
                        child = SubElement(file_element, sanitize_tag(file_key))
                        if isinstance(file_value, dict) or isinstance(file_value, list):
                            dict_to_xml(child, file_value)
                        else:
                            child.text = str(file_value)
                    elif file_key == 'type':
                        child = SubElement(file_element, sanitize_tag(file_key))
                        child.text = str(file_value)
            elif isinstance(value, dict):
                # Directory
                dir_element = SubElement(parent, 'directory', name=key)
                dict_to_xml(dir_element, value)
            elif isinstance(value, list):
                # If a list is present, e.g., for multiple files or directories
                for item in value:
                    if isinstance(item, dict):
                        dict_to_xml(parent, item)
            else:
                # Other types can be added as text
                child = SubElement(parent, sanitize_tag(key))
                child.text = str(value)
    elif isinstance(data, list):
        for item in data:
            dict_to_xml(parent, item)
    else:
        parent.text = str(data)

def prettify_xml(element: Element) -> str:
    """
    Returns a pretty-printed XML string for the Element.
    """
    rough_string = tostring(element, 'utf-8')
    try:
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    except Exception as e:
        logging.error(f"{Fore.RED}Error formatting XML: {e}{Style.RESET_ALL}")
        return rough_string.decode('utf-8')

def output_to_xml(data: Dict[str, Any], output_file: str) -> None:
    """
    Writes the data to an XML file with improved structure and readability.
    """
    try:
        logging.debug(f"Starting XML conversion with data: {data}")
        root = Element('repository')
        dict_to_xml(root, data)

        pretty_xml = prettify_xml(root)
        logging.debug(f"XML structure after conversion: {pretty_xml[:200]}...")  # because its a shitty format

        with open(output_file, 'w', encoding='utf-8') as xml_file:
            xml_file.write(pretty_xml)
        
        logging.info(f"XML output successfully written to '{output_file}'.")
    except Exception as e:
        logging.error(
            f"{Fore.RED}Error converting data to XML: {e}{Style.RESET_ALL}"
        )
