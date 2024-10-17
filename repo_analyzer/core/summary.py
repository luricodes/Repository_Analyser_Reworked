# repo_analyzer/core/summary.py

from typing import Any, Dict, Optional

def create_summary(
    structure: Dict[str, Any],
    summary: Dict[str, Any],
    include_summary: bool,
    hash_algorithm: Optional[str] = None  # Neuer Parameter
) -> Dict[str, Any]:
    """
    Erstellt die Zusammenfassung der Verzeichnisstruktur.

    Args:
        structure (Dict[str, Any]): Die Verzeichnisstruktur.
        summary (Dict[str, Any]): Die vorhandene Zusammenfassung.
        include_summary (bool): Flag, ob die Zusammenfassung eingeschlossen werden soll.
        hash_algorithm (Optional[str], optional): Der verwendete Hash-Algorithmus oder None.

    Returns:
        Dict[str, Any]: Die endgültige Datenstruktur für die Ausgabe.
    """
    if include_summary and summary:
        output_data = {
            "summary": summary,
            "hash_algorithm": hash_algorithm,
            "structure": structure,
        }
    else:
        output_data = structure
    return output_data
