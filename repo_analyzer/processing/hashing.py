# repo_analyzer/processing/hashing.py

import hashlib
import logging
from pathlib import Path
from typing import Optional

# Optional: Farbliche Hervorhebung in Logs beibehalten
# Falls Farben nicht benötigt werden, können die folgenden Zeilen entfernt werden
from colorama import Fore, Style, init

# Initialisierung von colorama
init(autoreset=True)


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Berechnet den Hash einer Datei basierend auf dem angegebenen Algorithmus.

    Args:
        file_path (Path): Der Pfad zur Datei.
        algorithm (str, optional): Der Hash-Algorithmus (z.B. 'md5', 'sha1', 'sha256'). 
                                   Standard ist 'sha256'.

    Returns:
        Optional[str]: Der Hash der Datei als Hex-String oder None bei Fehlern.
    """
    if not algorithm:
        logging.error("Kein Hash-Algorithmus angegeben.")
        return None

    algorithm = algorithm.lower()
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        logging.error(f"{Fore.RED}Ungültiger Hash-Algorithmus: {algorithm}{Style.RESET_ALL}")
        return None

    try:
        with file_path.open('rb') as file:
            for chunk in iter(lambda: file.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        logging.warning(f"{Fore.YELLOW}Datei nicht gefunden: {file_path}{Style.RESET_ALL}")
    except PermissionError:
        logging.warning(f"{Fore.YELLOW}Keine Berechtigung zum Lesen der Datei: {file_path}{Style.RESET_ALL}")
    except OSError as e:
        logging.warning(f"{Fore.YELLOW}OS-Fehler beim Lesen der Datei {file_path}: {e}{Style.RESET_ALL}")
    
    return None
