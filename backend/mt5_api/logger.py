# logger.py
import sys
from datetime import datetime
from pprint import pformat
import time

# Windows: la console usa cp1252 e crasha (UnicodeEncodeError) sulle emoji.
# Forza UTF-8 sostituendo i caratteri non codificabili, così print() non fallisce.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

start_time = datetime.now()
logs = []  # lista globale dei log

# def log(message: str):
#     """Aggiunge un messaggio con timestamp relativo."""
#     elapsed = (datetime.now() - start_time).total_seconds()
#     timestamp = f"[+{elapsed:.1f}s]"
#     logs.append(f"{timestamp} {message}")
#     print(f"{timestamp} {message}")

def log(message):
    if isinstance(message, dict):
        message = pformat(message)
    elif not isinstance(message, str):
        message = str(message)

    for line in message.splitlines():
        print(f"[+{time.time():.1f}s] {line}")
