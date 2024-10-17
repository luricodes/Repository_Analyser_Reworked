# repo_analyzer/processing/hashing.py

import hashlib
import logging
from pathlib import Path
from typing import Optional

from colorama import Fore, Style

def compute_file_hash(file_path: Path, algorithm: Optional[str] = "md5") -> Optional[str]:
    """
    Berechnet den Hash einer Datei basierend auf dem angegebenen Algorithmus.

    Args:
        file_path (Path): Der Pfad zur Datei.
        algorithm (Optional[str]): Der Hash-Algorithmus (z.B. 'md5', 'sha1').

    Returns:
        Optional[str]: Der Hash der Datei als Hex-String oder None bei Fehlern.
    """
    if algorithm is None:
        return None
    algorithm = algorithm.lower()
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        logging.error(f"{Fore.RED}Ungültiger Hash-Algorithmus: {algorithm}{Style.RESET_ALL}")
        return None

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
