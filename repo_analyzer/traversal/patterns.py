# repo_analyzer/traversal/patterns.py

import fnmatch
import logging
import re
from functools import lru_cache
from typing import Pattern, Sequence

from colorama import Fore, Style

@lru_cache(maxsize=None)
def compile_regex(pattern: str) -> Pattern:
    """
    Compiles a regex pattern and caches it.

    Args:
        pattern (str): The regex pattern as a string.

    Returns:
        Pattern: The compiled regex pattern.
    """
    return re.compile(pattern)

def matches_patterns(filename: str, patterns: Sequence[str]) -> bool:
    """
    Checks if the filename matches any of the patterns (Glob or Regex).

    Args:
        filename (str): The name of the file.
        patterns (Sequence[str]): A sequence of patterns (Glob or Regex).

    Returns:
        bool: True if the filename matches any of the patterns, otherwise False.
    """
    for pattern in patterns:
        if pattern.startswith('regex:'):
            regex: str = pattern[len('regex:'):]
            try:
                compiled: Pattern = compile_regex(regex)
                if compiled.match(filename):
                    return True
            except re.error as e:
                logging.error(
                    f"{Fore.RED}Invalid regex pattern '{regex}': {e}{Style.RESET_ALL}"
                )
        else:
            if fnmatch.fnmatch(filename, pattern):
                return True
    return False
