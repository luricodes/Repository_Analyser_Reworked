# repo_analyzer/utils/helpers.py

import logging
from colorama import Fore, Style
from pathlib import Path


def is_binary_alternative(file_path: Path) -> bool:
    """
    Alternative Methode zur Binärdatei-Erkennung:
    Prüft, ob die Datei NULL-Bytes enthält.
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
        return False
    except Exception as e:
        logging.error(f"{Fore.RED}Fehler bei der alternativen Binärprüfung für {file_path}: {e}{Style.RESET_ALL}")
        return False
