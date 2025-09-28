import os
import datetime
import glob
import warnings
import sys

LOG_FILE = "logs/app.log"

# Filter common torch/paddle warnings from logs
_FILTERED_WARNINGS = [
    "torch",
    "paddle",
    "CUDA",
    "cuDNN",
    "TensorFlow",
    "UserWarning: torch",
    "FutureWarning: torch",
    "DeprecationWarning: torch"
]

def _should_filter_message(msg):
    """Check if a message should be filtered from logs"""
    msg_lower = msg.lower()
    for warning_text in _FILTERED_WARNINGS:
        if warning_text.lower() in msg_lower and ("warning" in msg_lower or "deprecated" in msg_lower):
            return True
    return False

def log(msg):
    # Filter out torch/paddle warnings to keep logs clean
    if _should_filter_message(str(msg)):
        return
    
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


def setup_warning_filters():
    """Setup warning filters to suppress torch/paddle warnings globally"""
    # Suppress torch warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch") 
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    
    # Suppress paddle warnings  
    warnings.filterwarnings("ignore", category=UserWarning, module="paddle")
    warnings.filterwarnings("ignore", category=FutureWarning, module="paddle")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="paddle")
    
    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    
    log("Warning filters configured for cleaner logs")