import os
import datetime
import glob

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

def clear_logs():
    """Clear all log files in the logs directory."""
    try:
        logs_dir = os.path.dirname(LOG_FILE)
        if os.path.exists(logs_dir):
            # Remove all log files in the logs directory
            log_files = glob.glob(os.path.join(logs_dir, "*.log"))
            for log_file in log_files:
                if os.path.exists(log_file):
                    os.remove(log_file)
        
        # Create logs directory if it doesn't exist
        os.makedirs(logs_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error clearing logs: {e}")
        return False