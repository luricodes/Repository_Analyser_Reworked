# repo_analyzer/core/summary.py

from typing import Any, Dict

def create_summary(structure: Dict[str, Any], summary: Dict[str, Any], include_summary: bool) -> Dict[str, Any]:
    """
    Erstellt die Zusammenfassung der Verzeichnisstruktur.

    Args:
        structure (Dict[str, Any]): Die Verzeichnisstruktur.
        summary (Dict[str, Any]): Die vorhandene Zusammenfassung.
        include_summary (bool): Flag, ob die Zusammenfassung eingeschlossen werden soll.

    Returns:
        Dict[str, Any]: Die endgültige Datenstruktur für die Ausgabe.
    """
    if include_summary and summary:
        output_data = {
            "summary": summary,
            "structure": structure,
        }
    else:
        output_data = structure
    return output_data
