# Repo Analyzer

Ein Tool zur Analyse von Repository-Strukturen und Ausgabe in verschiedenen Formaten (JSON, YAML, XML).

## Installation

Verwenden Sie `pip`, um das Paket zu installieren:

```bash
pip install -e .


## Nutzung

### Optionen für die Hash-Verifizierung

- **Hash-Algorithmus auswählen:**

  Sie können den Hash-Algorithmus mit der Option `--hash-algorithm` auswählen. Unterstützte Algorithmen sind:

  - `md5` (Standard)
  - `sha1`
  - `sha256`
  - `sha512`

  **Beispiel:**

  ```bash
  repo_analyzer /pfad/zum/repo --hash-algorithm sha256 --max-size 50 -o ausgabe.json

### Vollständige CLI-Optionen
usage: repo_analyzer [-h] [-o OUTPUT] [-m MAX_SIZE] [--include-binary]
                     [--exclude-folders [EXCLUDE_FOLDERS ...]]
                     [--exclude-files [EXCLUDE_FILES ...]]
                     [--exclude-patterns [EXCLUDE_PATTERNS ...]]
                     [--verbose] [--follow-symlinks]
                     [--image-extensions [IMAGE_EXTENSIONS ...]]
                     [--include-summary] [-f {json,yaml,xml}]
                     [--threads THREADS] [--config CONFIG]
                     [--log-file LOG_FILE]
                     [--encoding ENCODING]
                     [--hash-algorithm {md5,sha1,sha256,sha512}]
                     [--no-hash]

Ein Tool zur Analyse von Repository-Strukturen und Ausgabe in verschiedenen Formaten (JSON, YAML, XML).

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Name der Ausgabedatei (Standard: repository_structure.json).
  -m MAX_SIZE, --max-size MAX_SIZE
                        Maximale Dateigröße in Bytes, bis zu der der Inhalt gelesen wird
                        (Standard: 52428800 Bytes).
  --include-binary     Schließt binäre Dateien (einschließlich Bilddateien) in die
                        Ausgabe ein.
  --exclude-folders [EXCLUDE_FOLDERS ...]
                        Zusätzliche Ordner, die ausgeschlossen werden sollen
                        (z.B. --exclude-folders folder1 folder2).
  --exclude-files [EXCLUDE_FILES ...]
                        Zusätzliche Dateien, die ausgeschlossen werden sollen
                        (z.B. --exclude-files file1.txt file2.log).
  --exclude-patterns [EXCLUDE_PATTERNS ...]
                        Glob- oder Regex-Muster zum Ausschließen von Dateien und
                        Ordnern (z.B. *.log, regex:^temp_). Regex-Muster müssen mit
                        'regex:' beginnen.
  --verbose            Erhöht die Ausgabe von Informationen (DEBUG-Level).
  --follow-symlinks    Folgt symbolischen Links während des Verzeichnisdurchlaufs.
  --image-extensions [IMAGE_EXTENSIONS ...]
                        Zusätzliche Bilddateiendungen, die berücksichtigt werden sollen
                        (z.B. --image-extensions .ico .eps).
  --include-summary    Fügt eine Zusammenfassung der Dateien in die Ausgabe ein.
  -f {json,yaml,xml}, --format {json,yaml,xml}
                        Format der Ausgabedatei (Standard: json).
  --threads THREADS    Anzahl der Threads für die parallele Verarbeitung
                        (Standard: dynamisch basierend auf der CPU-Anzahl).
  --config CONFIG      Pfad zu einer Konfigurationsdatei (YAML oder JSON).
  --log-file LOG_FILE  Pfad zu einer Logdatei. Wenn angegeben, werden Logs
                        zusätzlich in diese Datei geschrieben.
  --encoding ENCODING  Standard-Encoding für das Lesen von Textdateien (Standard:
                        utf-8).
  --hash-algorithm {md5,sha1,sha256,sha512}
                        Hash-Algorithmus zur Verifizierung von Dateien (Standard:
                        md5).
  --no-hash            Deaktiviert die Hash-Verifizierung und arbeitet ohne Hash.


## SQLite Cache Management

Das Modul `sqlite_cache.py` verwaltet den Cache der Repository-Analyse mithilfe von SQLite. Es verwendet einen Verbindungspool, um die Effizienz und Thread-Sicherheit bei Datenbankzugriffen zu gewährleisten.

### Funktionen

- `initialize_connection_pool(db_path: str, pool_size: Optional[int] = None) -> None`
  - Initialisiert den Verbindungspool mit der angegebenen Anzahl von Verbindungen.

- `get_cached_entry(file_path: str) -> Optional[Dict[str, Any]]`
  - Ruft den zwischengespeicherten Eintrag für einen gegebenen Dateipfad ab.

- `set_cached_entry(file_path: str, file_hash: Optional[str], hash_algorithm: Optional[str], file_info: Dict[str, Any], size: int, mtime: float) -> None`
  - Setzt oder aktualisiert den zwischengespeicherten Eintrag für einen gegebenen Dateipfad.

- `clean_cache(root_dir: Path) -> None`
  - Bereinigt den Cache, indem Einträge für Dateien entfernt werden, die nicht mehr existieren.

- `close_all_connections() -> None`
  - Schließt alle SQLite-Verbindungen im Verbindungspool ordnungsgemäß.

### Nutzung des sqlite_cache Verbindungspools

```python
from repo_analyzer.cache.sqlite_cache import initialize_connection_pool, get_cached_entry, set_cached_entry, clean_cache, close_all_connections
from pathlib import Path

# Initialisiere den Verbindungspool
initialize_connection_pool("path/to/cache.db", pool_size=10)

# Setze einen Cache-Eintrag
set_cached_entry("/path/to/file.txt", "hash123", "sha256", {"content": "data"}, 1024, 1610000000.0)

# Hole einen Cache-Eintrag
entry = get_cached_entry("/path/to/file.txt")
print(entry)

# Bereinige den Cache basierend auf dem Root-Verzeichnis
clean_cache(Path("/path/to/root_dir"))

# Schließe alle Verbindungen beim Beenden des Programms
close_all_connections()
