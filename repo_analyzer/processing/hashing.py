# repo_analyzer/processing/hashing.py

import hashlib
import logging
from pathlib import Path
from typing import Optional

from colorama import Fore, Style


def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Berechnet den MD5-Hash einer Datei.

    Args:
        file_path (Path): Der Pfad zur Datei,
        deren Hash berechnet werden soll.

    Returns:
        Optional[str]: Der MD5-Hash der Datei als Hex-String
        oder None, falls ein Fehler auftritt.
    """
    hasher = hashlib.md5()
    try:
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (FileNotFoundError, PermissionError, OSError) as e:
        logging.warning(
            f"{Fore.YELLOW}Konnte Hash nicht berechnen für: {file_path} - {e}{Style.RESET_ALL}"
        )
        return None
