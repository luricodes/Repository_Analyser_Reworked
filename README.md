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
