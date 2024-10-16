# repo_analyzer/traversal/patterns.py

import fnmatch
import re
import logging
from colorama import Fore, Style
from typing import List

def compile_regex(pattern: str):
    """
    Kompiliert ein Regex-Muster und cached es.
    """
    return re.compile(pattern)

def matches_patterns(filename: str, patterns: List[str]) -> bool:
    """
    Prüft, ob der Dateiname einem der Muster entspricht (Glob oder Regex).
    """
    for pattern in patterns:
        if pattern.startswith('regex:'):
            regex = pattern[len('regex:'):]
            try:
                compiled = compile_regex(regex)
                if compiled.match(filename):
                    return True
            except re.error as e:
                logging.error(f"{Fore.RED}Ungültiges Regex-Muster '{regex}': {e}{Style.RESET_ALL}")
        else:
            if fnmatch.fnmatch(filename, pattern):
                return True
    return False