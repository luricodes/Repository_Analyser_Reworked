# repo_analyzer/cli/parser.py

import argparse
import os
from pathlib import Path

def get_default_cache_path() -> str:
    """
    Gibt den Standardpfad für das Cache-Verzeichnis zurück.
    """
    home = Path.home()
    return str(home / "Documents" / "Datenbank") if os.name == 'nt' else str(home / ".repo_analyzer" / "cache")

def parse_arguments():
    """
    Parst die Kommandozeilenargumente und gibt die konfigurierten Argumente zurück.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Listet ein Repository in einer JSON-, YAML-, XML- oder NDJSON-Datei auf."
        ),
        epilog=(
            "Beispiele:\\n"
            "  repo_analyzer /pfad/zum/repo -o output.json\\n"
            "  repo_analyzer --exclude-folders build dist --include-binary --format yaml\\n"
            "  repo_analyzer /pfad/zum/repo -o output.ndjson --format ndjson --stream\\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Pflichtargument: root_directory
    parser.add_argument(
        "root_directory",
        type=str,
        help="Das Wurzelverzeichnis des zu analysierenden Repositorys."
    )
    
    # Optionale Argumente
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Pfad zur Ausgabedatei."
    )
    parser.add_argument(
        "--hash-algorithm",
        type=str,
        choices=["md5", "sha1", "sha256", "sha512"],
        default="md5",
        help="Hash-Algorithmus zur Verifizierung (Standard: md5)."
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Beinhaltet binäre Dateien und Bilddateien in der Analyse."
    )
    parser.add_argument(
        "--exclude-folders",
        nargs='*',
        default=[],
        help="Liste von Ordnernamen, die von der Analyse ausgeschlossen werden sollen."
    )
    parser.add_argument(
        "--exclude-files",
        nargs='*',
        default=[],
        help="Liste von Dateinamen, die von der Analyse ausgeschlossen werden sollen."
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Folgt symbolischen Links während der Traversierung."
    )
    parser.add_argument(
        "--image-extensions",
        nargs='*',
        default=[],
        help="Zusätzliche Bilddateiendungen, die als binär betrachtet werden sollen."
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs='*',
        default=[],
        help="Glob- oder Regex-Muster zum Ausschließen von Dateien und Ordnern."
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Anzahl der Threads für die parallele Verarbeitung (Standard: CPU-Kerne * 2)."
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default='utf-8',
        help="Standard-Encoding für Textdateien (Standard: utf-8)."
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Aktiviert den Streaming-Modus für die Ausgabe (nur für JSON und NDJSON).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Aktiviert ausführliches Logging."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Pfad zur Logdatei."
    )
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="Deaktiviert die Hash-Verifizierung."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Pfad zur Konfigurationsdatei."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Maximale Dateigröße zum Lesen in MB (überschreibt Konfigurationsdatei)."
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        default=5,
        help="Größe des Datenbank-Verbindungspools (Standard: 5)."
    )
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Fügt eine Zusammenfassung der Analyse zur Ausgabedatei hinzu."
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "yaml", "xml", "ndjson"],  # NDJSON hinzugefügt
        default="json",
        help="Format der Ausgabedatei (Standard: json).",
    )
    parser.add_argument(
        "--cache-path",
        type=str,
        default=get_default_cache_path(),
        help="Pfad zum Cache-Verzeichnis (Standard: ~/.repo_analyzer/cache)."
    )
    
    args = parser.parse_args()

    # Automatische Dateiendung hinzufügen, falls nicht vorhanden
    if not args.output.endswith(f".{args.format}"):
        args.output += f".{args.format}"

    return args
