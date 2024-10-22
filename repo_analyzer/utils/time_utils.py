import datetime
import logging
from typing import Any

def format_timestamp(timestamp: Any) -> str:
    """
    Formatiert einen Timestamp in ISO 8601 Format.
    """
    if isinstance(timestamp, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(timestamp).isoformat()
        except (OSError, OverflowError, ValueError):
            logging.warning(f"Ungültiger Timestamp: {timestamp}")
            return ""
    return ""
