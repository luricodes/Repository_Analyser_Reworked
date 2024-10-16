from ..config.defaults import DEFAULT_MAX_FILE_SIZE
# repo_analyzer/cli/parser.py

import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Listet ein Repository in einer JSON-, YAML- oder XML-Datei auf.",
        epilog="Beispiele:\n"
               "  python script.py /path/to/repo -o output.json\n"
               "  python script.py --exclude-folders build dist --include-binary --format yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "root_directory",
        nargs="?",
        default=".",
        help="Das Wurzelverzeichnis des zu durchsuchenden Repositories (Standard: aktuelles Verzeichnis)."
    )
    parser.add_argument(
        "-o", "--output",
        default="repository_structure.json",
        help="Name der Ausgabedatei (Standard: repository_structure.json)."
    )
    parser.add_argument(
        "-m", "--max-size",
        type=int,
        default=DEFAULT_MAX_FILE_SIZE,  # Importiere DEFAULT_MAX_FILE_SIZE aus defaults.py
        help=f"Maximale Dateigröße in Bytes, bis zu der der Inhalt gelesen wird (Standard: {DEFAULT_MAX_FILE_SIZE} Bytes)."
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Schließt binäre Dateien (einschließlich Bilddateien) in die Ausgabe ein."
    )
    parser.add_argument(
        "--exclude-folders",
        nargs='*',
        default=[],
        help="Zusätzliche Ordner, die ausgeschlossen werden sollen (z.B. --exclude-folders folder1 folder2)."
    )
    parser.add_argument(
        "--exclude-files",
        nargs='*',
        default=[],
        help="Zusätzliche Dateien, die ausgeschlossen werden sollen (z.B. --exclude-files file1.txt file2.log)."
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs='*',
        default=[],
        help="Glob- oder Regex-Muster zum Ausschließen von Dateien und Ordnern (z.B. *.log, regex:^temp_). Regex-Muster müssen mit 'regex:' beginnen."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Erhöht die Ausgabe von Informationen (DEBUG-Level)."
    )
    # Neue Argumente
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Folgt symbolischen Links während des Verzeichnisdurchlaufs."
    )
    parser.add_argument(
        "--image-extensions",
        nargs='*',
        default=[],
        help="Zusätzliche Bilddateiendungen, die berücksichtigt werden sollen (z.B. --image-extensions .ico .eps)."
    )
    # Neue Option für die Zusammenfassung
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Fügt eine Zusammenfassung der Dateien in die Ausgabe ein."
    )
    # Unterstützung zusätzlicher Ausgabeformate
    parser.add_argument(
        "-f", "--format",
        choices=['json', 'yaml', 'xml'],
        default='json',
        help="Format der Ausgabedatei (Standard: json)."
    )
    # Option für die Anzahl der Threads (dynamisch festgelegt)
    parser.add_argument(
        "--threads",
        type=int,
        default=None,  # Dynamische Standardanzahl
        help="Anzahl der Threads für die parallele Verarbeitung (Standard: dynamisch basierend auf der CPU-Anzahl)."
    )
    # Option für die Konfigurationsdatei
    parser.add_argument(
        "--config",
        type=str,
        help="Pfad zu einer Konfigurationsdatei (YAML oder JSON)."
    )
    # Option für das Logfile
    parser.add_argument(
        "--log-file",
        type=str,
        help="Pfad zu einer Logdatei. Wenn angegeben, werden Logs zusätzlich in diese Datei geschrieben."
    )
    # Neues Argument für Encoding
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8",
        help="Standard-Encoding für das Lesen von Textdateien (Standard: utf-8)."
    )

    args = parser.parse_args()
    return args