# Repo Analyzer

Ein Tool zur Analyse von Repository-Strukturen und Ausgabe in verschiedenen Formaten (JSON, YAML, XML).

## Installation

Verwenden Sie `pip`, um das Paket zu installieren:

```bash
pip install -e .


Repository Struktur
repo_analyzer/
│
├── core/
│   ├── __init__.py
│   ├── application.py
│   └── summary.py
│
├── cache/
│   ├── __init__.py
│   └── sqlite_cache.py
│
├── cli/
│   ├── __init__.py
│   └── parser.py
│
├── config/
│   ├── __init__.py
│   ├── defaults.py
│   └── loader.py
│
├── gui/
│   ├── __init__.py
│   ├── controllers.py
│   ├── dialogs.py
│   ├── main_window.py
│   └── widgets.py
│
├── logging/
│   ├── __init__.py
│   └── setup.py
│
├── output/
│   ├── __init__.py
│   ├── output_factory.py
│   ├── json_output.py
│   ├── yaml_output.py
│   └── xml_output.py
│
├── processing/
│   ├── __init__.py
│   ├── file_processor.py
│   └── hashing.py
│
├── traversal/
│   ├── __init__.py
│   ├── patterns.py
│   └── traverser.py
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py
│   └── mime_type.py
│
├── tests/
│   ├── __init__.py
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_logging.py
│   ├── test_output.py
│   ├── test_processing.py
│   └── test_traversal.py
│
├── README.md
├── requirements.txt
└── setup.py
