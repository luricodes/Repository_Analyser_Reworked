# **Repo Analyzer**

Repo Analyzer ist ein Tool zur Analyse von Repository-Strukturen und unterstützt mehrere Ausgabeformate, darunter JSON, YAML, XML und NDJSON. Es ist nützlich für die Analyse großer Verzeichnisse, das Erstellen von Verzeichnisstrukturen und das Zwischenspeichern von Informationen mithilfe einer SQLite-Datenbank.


## **Inhaltsverzeichnis**

- [Installation](#installation)
- [Verwendung](#verwendung)
- [Features](#features)
- [Kommandozeilenoptionen](#kommandozeilenoptionen)
- [Ausgabeformate](#ausgabeformate)
- [Beispiel](#beispiel)
- [Konfiguration](#konfiguration)
- [Lizenz](#lizenz)


## **Installation**

1. Klone das Repository:
```bash
git clone https://github.com/dein-repo/repo_analyzer.git
```
2. Navigiere in das Verzeichnis:
```bash
cd repo_analyzer
```
3. Installiere die Abhängigkeiten:
```bash
pip install -r requirements.txt
```
4. Installiere das Tool:
```bash
python setup.py install
```


## **Verwendung**

Das Tool wird über die Kommandozeile aufgerufen und benötigt ein Root-Verzeichnis, das analysiert werden soll, sowie ein Ausgabedateipfad.

Beispiel:
```bash
repo_analyzer /pfad/zum/repo -o output.json --format json --include-binary
```


## **Features**

- **Mehrere Ausgabeformate**: JSON, YAML, XML, NDJSON
- **Parallele Verarbeitung**: Beschleunigung durch Nutzung mehrerer Threads
- **Caching**: Zwischenspeicherung von Dateiinformationen in einer SQLite-Datenbank
- **Hash-Verifizierung**: Unterstützung von verschiedenen Hash-Algorithmen (MD5, SHA1, SHA256, SHA512)
- **Binärdateien-Unterstützung**: Optionale Einbeziehung von Binär- und Bilddateien


## **Kommandozeilenoptionen**

- `root_directory`: Das Wurzelverzeichnis des zu analysierenden Repositorys.
- `-o`, `--output`: Pfad zur Ausgabedatei.
- `--format`: Das Format der Ausgabedatei (json, yaml, xml, ndjson).
- `--include-binary`: Beinhaltet Binärdateien in der Analyse.
- `--threads`: Anzahl der Threads für die parallele Verarbeitung.
- `--cache-path`: Pfad zum Cache-Verzeichnis.

Weitere Optionen findest du mit:
```bash
repo_analyzer --help
```


## **Ausgabeformate**

- **JSON**: Standardausgabeformat, strukturiert die Verzeichnisstruktur in einem hierarchischen Format.
- **YAML**: Lesbares Format für Konfigurationsdateien.
- **XML**: Hierarchische Struktur, geeignet für Interoperabilität mit anderen Tools.
- **NDJSON**: Zeilenbasierte JSON-Ausgabe für Streaming und Big Data-Prozesse.


## **Beispiel**

```bash
repo_analyzer /pfad/zum/repo -o struktur.json --format json --threads 4 --include-binary
```

Das obige Beispiel analysiert das Verzeichnis `/pfad/zum/repo`, gibt die Struktur in die Datei `struktur.json` im JSON-Format aus und nutzt 4 Threads für die Verarbeitung.


## **Konfiguration**

Eine Konfigurationsdatei (JSON oder YAML) kann verwendet werden, um Standardwerte für die Analyse festzulegen. Diese Datei kann über die Option `--config` angegeben werden.

Beispielkonfigurationsdatei (YAML):
```yaml
max_size: 100
exclude_folders:
  - ".git"
  - "node_modules"
```


## **Lizenz**

Dieses Projekt steht unter der MIT-Lizenz.