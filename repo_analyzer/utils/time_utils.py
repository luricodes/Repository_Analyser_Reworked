import datetime
import logging
from typing import Any

def format_timestamp(timestamp: Any) -> str:
    """
    Formats a timestamp in ISO 8601 format.
    """
    if isinstance(timestamp, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(timestamp).isoformat()
        except (OSError, OverflowError, ValueError):
            logging.warning(f"Invalid timestamp: {timestamp}")
            return ""
    return ""
