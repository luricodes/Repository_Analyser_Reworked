# repo_analyzer/core/flags.py

import threading

# Thread-safe event for signalling a shutdown
shutdown_event = threading.Event()
