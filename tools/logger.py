import os
import datetime

LOG_FILE = "logs/app.log"

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | {msg}\n")
    # Also print to console for immediate visibility
    print(f"[LOG {timestamp}] {msg}")

def read_logs():
    if not os.path.exists(LOG_FILE):
        return "Brak logów."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()