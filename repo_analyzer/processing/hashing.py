# repo_analyzer/processing/hashing.py

import hashlib
import logging
from pathlib import Path
from typing import Optional

# Optional: Keep color highlighting in logs
# If colors are not needed, the following lines can be removed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Calculates the hash of a file based on the specified algorithm.

    Args:
        file_path (Path): The path to the file.
        algorithm (str, optional): The hash algorithm (e.g., 'md5', 'sha1', 'sha256'). 
                                   Default is 'sha256'.

    Returns:
        Optional[str]: The file's hash as a hex string or None in case of errors.
    """
    if not algorithm:
        logging.error("No hash algorithm specified.")
        return None

    algorithm = algorithm.lower()
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        logging.error(f"{Fore.RED}Invalid hash algorithm: {algorithm}{Style.RESET_ALL}")
        return None

    try:
        with file_path.open('rb') as file:
            for chunk in iter(lambda: file.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        logging.warning(f"{Fore.YELLOW}File not found: {file_path}{Style.RESET_ALL}")
    except PermissionError:
        logging.warning(f"{Fore.YELLOW}No permission to read the file: {file_path}{Style.RESET_ALL}")
    except OSError as e:
        logging.warning(f"{Fore.YELLOW}OS error when reading the file {file_path}: {e}{Style.RESET_ALL}")
    
    return None
