# repo_analyzer/output/output_factory.py

from typing import Callable, Dict, Any

from .json_output import output_to_json
from .yaml_output import output_to_yaml
from .xml_output import output_to_xml


class OutputFactory:
    """
    Factory zur Auswahl des Ausgabeformats basierend auf dem Benutzerinput.
    """

    _output_methods: Dict[str, Callable[[Dict[str, Any], str], None]] = {
        "json": output_to_json,
        "yaml": output_to_yaml,
        "xml": output_to_xml,
    }

    @classmethod
    def get_output(cls, format: str) -> Callable[[Dict[str, Any], str], None]:
        """
        Gibt die entsprechende Ausgabe-Methode zurück.

        Args:
            format (str): Das gewünschte Ausgabeformat.

        Returns:
            Callable[[Dict[str, Any], str], None]: Die Ausgabe-Methode.
        """
        try:
            return cls._output_methods[format]
        except KeyError:
            raise ValueError(f"Unbekanntes Ausgabeformat: {format}")
