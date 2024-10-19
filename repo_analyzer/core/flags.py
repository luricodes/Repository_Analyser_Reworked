# repo_analyzer/core/flags.py

import threading

# Thread-sicheres Event zur Signalisierung eines Shutdowns
shutdown_event = threading.Event()
