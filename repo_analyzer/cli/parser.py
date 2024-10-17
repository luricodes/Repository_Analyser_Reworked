# repo_analyzer/cli/parser.py

"""
Dieses Modul enthält die Funktion zur Argumentenparsing für das Repository-Analyse-Tool.
"""

import argparse

from ..config.defaults import DEFAULT_MAX_FILE_SIZE


def parse_arguments():
    """
    Parst die Kommandozeilenargumente und gibt die konfigurierten Argumente zurück.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Listet ein Repository in einer JSON-, YAML- oder XML-Datei auf."
        ),
        epilog=(
            "Beispiele:\\n"
            "  repo_analyzer /pfad/zum/repo -o output.json\\n"
            "  repo_analyzer --exclude-folders build dist --include-binary --format yaml\\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Wurzelverzeichnis
    parser.add_argument(
        "root_directory",
        nargs="?",
        default=".",
        help=(
            "Das Wurzelverzeichnis des zu durchsuchenden Repositories "
            "(Standard: aktuelles Verzeichnis)."
        ),
    )
    
    # Ausgabedatei
    parser.add_argument(
        "-o",
        "--output",
        default="repository_structure.json",
        help="Name der Ausgabedatei (Standard: repository_structure.json).",
    )
    
    # Maximalgröße der Dateien
    parser.add_argument(
        "-m",
        "--max-size",
        type=int,
        default=None,
        help=(
            f"Maximale Dateigröße in MB, bis zu der der Inhalt gelesen wird "
            f"(Standard: {DEFAULT_MAX_FILE_SIZE // (1024 * 1024)} MB aus defaults.py)."
        ),
    )
    
    #Weitere Argumente
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Schließt binäre Dateien (einschließlich Bilddateien) in die Ausgabe ein.",
    )
    parser.add_argument(
        "--exclude-folders",
        nargs="*",
        default=[],
        help=(
            "Zusätzliche Ordner, die ausgeschlossen werden sollen "
            "(z.B. --exclude-folders folder1 folder2)."
        ),
    )
    parser.add_argument(
        "--exclude-files",
        nargs="*",
        default=[],
        help=(
            "Zusätzliche Dateien, die ausgeschlossen werden sollen "
            "(z.B. --exclude-files file1.txt file2.log)."
        ),
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs="*",
        default=[],
        help=(
            "Glob- oder Regex-Muster zum Ausschließen von Dateien und Ordnern "
            "(z.B. *.log, regex:^temp_). Regex-Muster müssen mit 'regex:' beginnen."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Erhöht die Ausgabe von Informationen (DEBUG-Level).",
    )
    # Neue Argumente
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Folgt symbolischen Links während des Verzeichnisdurchlaufs.",
    )
    parser.add_argument(
        "--image-extensions",
        nargs="*",
        default=[],
        help=(
            "Zusätzliche Bilddateiendungen, die berücksichtigt werden sollen "
            "(z.B. --image-extensions .ico .eps)."
        ),
    )
    # Neue Option für die Zusammenfassung
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Fügt eine Zusammenfassung der Dateien in die Ausgabe ein.",
    )
    # Unterstützung zusätzlicher Ausgabeformate
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "yaml", "xml"],
        default="json",
        help="Format der Ausgabedatei (Standard: json).",
    )
    # Option für die Anzahl der Threads (dynamisch festgelegt)
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help=(
            "Anzahl der Threads für die parallele Verarbeitung "
            "(Standard: dynamisch basierend auf der CPU-Anzahl)."
        ),
    )
    # Option für die Konfigurationsdatei
    parser.add_argument(
        "--config",
        type=str,
        help="Pfad zu einer Konfigurationsdatei (YAML oder JSON).",
    )
    # Option für das Logfile
    parser.add_argument(
        "--log-file",
        type=str,
        help=(
            "Pfad zu einer Logdatei. Wenn angegeben, werden Logs "
            "zusätzlich in diese Datei geschrieben."
        ),
    )
    # Neues Argument für Encoding
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8",
        help="Standard-Encoding für das Lesen von Textdateien (Standard: utf-8).",
    )
    # Neue, gegenseitig ausschließende Argumente für Hash-Optionen
    hash_group = parser.add_mutually_exclusive_group()
    hash_group.add_argument(
        "--hash-algorithm",
        type=str,
        choices=["md5", "sha1", "sha256", "sha512"],
        default="md5",
        help="Hash-Algorithmus zur Verifizierung von Dateien (Standard: md5).",
    )
    hash_group.add_argument(
        "--no-hash",
        action="store_true",
        help="Deaktiviert die Hash-Verifizierung und arbeitet ohne Hash.",
    )

    args = parser.parse_args()
    return args
