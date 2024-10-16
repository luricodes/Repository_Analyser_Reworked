# repo_analyzer/processing/hashing.py

import hashlib
from pathlib import Path
import logging
from colorama import Fore, Style
from typing import Optional

def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Berechnet den MD5-Hash einer Datei.
    """
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.warning(f"{Fore.YELLOW}Konnte Hash nicht berechnen für: {file_path} - {e}{Style.RESET_ALL}")
        return None