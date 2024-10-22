# repo_analyzer/output/output_factory.py

from typing import Callable, Dict, Any

from .json_output import output_to_json, output_to_json_stream
from .yaml_output import output_to_yaml
from .xml_output import output_to_xml
from .ndjson_output import output_to_ndjson
from .dot_output import output_to_dot
from .csv_output import output_to_csv

class OutputFactory:
    """
    Factory-Klasse zur Erzeugung von Ausgabemethoden basierend auf dem gewünschten Format.
    """
    _output_methods: Dict[str, Callable[..., None]] = {
        "json": output_to_json,
        "json_stream": output_to_json_stream,
        "yaml": output_to_yaml,
        "xml": output_to_xml,
        "ndjson": output_to_ndjson,
        "dot": output_to_dot,
        "csv": output_to_csv,
    }

    @classmethod
    def get_output(cls, format: str, streaming: bool = False) -> Callable[..., None]:
        """
        Gibt die passende Ausgabefunktion basierend auf dem Format zurück.

        :param format: Das gewünschte Ausgabeformat.
        :param streaming: Gibt an, ob der Streaming-Modus verwendet werden soll.
        :return: Die entsprechende Ausgabefunktion.
        :raises ValueError: Wenn das Format unbekannt ist.
        """
        try:
            if streaming and format == "json":
                return cls._output_methods["json_stream"]
            return cls._output_methods[format]
        except KeyError:
            available = ', '.join(cls._output_methods.keys())
            raise ValueError(f"Unbekanntes Ausgabeformat: {format}. Verfügbare Formate sind: {available}.")
