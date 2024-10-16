# repo_analyzer/traversal/patterns.py

import fnmatch
import logging
import re
from functools import lru_cache
from typing import List, Pattern

from colorama import Fore, Style


@lru_cache(maxsize=None)
def compile_regex(pattern: str) -> Pattern:
    """
    Kompiliert ein Regex-Muster und cached es.

    Args:
        pattern (str): Das Regex-Muster als String.

    Returns:
        Pattern: Das kompilierte Regex-Muster.
    """
    return re.compile(pattern)


def matches_patterns(filename: str, patterns: List[str]) -> bool:
    """
    Prüft, ob der Dateiname einem der Muster entspricht (Glob oder Regex).

    Args:
        filename (str): Der Name der Datei.
        patterns (List[str]): Eine Liste von Mustern (Glob oder Regex).

    Returns:
        bool: True, wenn der Dateiname einem der Muster entspricht, sonst False.
    """
    for pattern in patterns:
        if pattern.startswith('regex:'):
            regex = pattern[len('regex:'):]
            try:
                compiled = compile_regex(regex)
                if compiled.match(filename):
                    return True
            except re.error as e:
                logging.error(
                    f"{Fore.RED}Ungültiges Regex-Muster '{regex}': {e}{Style.RESET_ALL}"
                )
        else:
            if fnmatch.fnmatch(filename, pattern):
                return True
    return False
