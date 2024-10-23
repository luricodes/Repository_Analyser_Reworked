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
    Factory class for creating output methods based on the desired format.
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
        try:
            if streaming and format == "json":
                return cls._output_methods["json_stream"]
            return cls._output_methods[format]
        except KeyError:
            available = ', '.join(cls._output_methods.keys())
            raise ValueError(f"Unknown output format: {format}. Available formats are: {available}.")
