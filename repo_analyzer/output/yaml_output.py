# repo_analyzer/output/yaml_output.py

import logging
from typing import Any, Dict
from pathlib import Path
import tempfile
import shutil

from colorama import Fore, Style
import yaml


class YAMLError(Exception):
    """Custom exception for YAML-related errors."""
    pass


def output_to_yaml(data: Dict[str, Any], output_file: str, **yaml_options) -> None:
    """
    Schreibt die Daten in eine YAML-Datei mit erweiterten Optionen, atomaren Schreibvorgängen und verbesserter Fehlerbehandlung.

    Args:
        data (Dict[str, Any]): Die Daten, die in die YAML-Datei geschrieben werden sollen.
        output_file (str): Der Pfad zur Ausgabedatei.
        **yaml_options: Zusätzliche Optionen für das YAML-Dump, z.B. default_flow_style.
    """
    default_options = {
        'allow_unicode': True,
        'sort_keys': False,
        'default_flow_style': False,  # Verbessert die Lesbarkeit durch Block-Stil
        'width': 4096,  # Erhöht die maximale Zeilenbreite, um lange Listen zu vermeiden
    }
    # Update default options mit benutzerdefinierten Optionen, falls vorhanden
    dump_options = {**default_options, **yaml_options}

    try:
        # Validierung der Daten
        validate_data(data)

        # Atomare Schreiboperation: Schreiben in eine temporäre Datei und Umbenennen
        temp_dir = Path(output_file).parent
        with tempfile.NamedTemporaryFile('w', delete=False, dir=temp_dir, encoding='utf-8') as temp_file:
            yaml.dump(data, temp_file, **dump_options)
            temp_file_path = Path(temp_file.name)

        # Umbenennen der temporären Datei zur endgültigen Ausgabedatei
        shutil.move(str(temp_file_path), output_file)

        logging.info(f"YAML-Ausgabe erfolgreich in '{output_file}' geschrieben.")
    except yaml.YAMLError as e:
        logging.error(
            f"{Fore.RED}YAML-Fehler beim Dumpen der Daten in '{output_file}': {e}{Style.RESET_ALL}"
        )
        raise YAMLError(f"YAML-Fehler: {e}") from e
    except (IOError, OSError) as e:
        logging.error(
            f"{Fore.RED}Fehler beim Schreiben der YAML-Ausgabedatei '{output_file}': {e}{Style.RESET_ALL}"
        )
        raise
    except Exception as e:
        logging.error(
            f"{Fore.RED}Unerwarteter Fehler beim Schreiben der YAML-Ausgabedatei '{output_file}': {e}{Style.RESET_ALL}"
        )
        raise


def validate_data(data: Any) -> None:
    """
    Validiert, ob die Daten YAML-kompatibel sind.

    Args:
        data (Any): Die zu validierenden Daten.

    Raises:
        YAMLError: Wenn die Daten nicht YAML-kompatibel sind.
    """
    try:
        # Versucht, die Daten zu serialisieren, ohne sie zu speichern
        yaml.safe_dump(data)  # Korrekt ohne Dumper-Parameter
    except yaml.YAMLError as e:
        raise YAMLError(f"Daten sind nicht YAML-kompatibel: {e}") from e
