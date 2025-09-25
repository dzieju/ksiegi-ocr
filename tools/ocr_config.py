"""
OCR engine configuration management
"""
import json
import os
from tools.logger import log

OCR_CONFIG_FILE = "ocr_config.json"

# Default OCR configuration
DEFAULT_OCR_CONFIG = {
    "engine": "tesseract",  # tesseract, easyocr, paddleocr
    "use_gpu": False,       # Try to use GPU if available
    "multiprocessing": True, # Use multiprocessing for OCR operations
    "max_workers": None     # None = auto-detect CPU count
}

class OCRConfig:
    """Handles OCR configuration persistence and management"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """Load OCR configuration from file or create default"""
        try:
            if os.path.exists(OCR_CONFIG_FILE):
                with open(OCR_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Ensure all required keys exist
                    for key, default_value in DEFAULT_OCR_CONFIG.items():
                        if key not in config:
                            config[key] = default_value
                    log(f"Załadowano konfigurację OCR: {config}")
                    return config
            else:
                log("Tworzenie domyślnej konfiguracji OCR")
                return DEFAULT_OCR_CONFIG.copy()
        except Exception as e:
            log(f"Błąd ładowania konfiguracji OCR: {e}, używam domyślnej")
            return DEFAULT_OCR_CONFIG.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(OCR_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            log(f"Zapisano konfigurację OCR: {self.config}")
            return True
        except Exception as e:
            log(f"Błąd zapisywania konfiguracji OCR: {e}")
            return False
    
    def get_engine(self):
        """Get current OCR engine"""
        return self.config.get("engine", "tesseract")
    
    def set_engine(self, engine):
        """Set OCR engine"""
        if engine in ["tesseract", "easyocr", "paddleocr"]:
            self.config["engine"] = engine
            return True
        return False
    
    def get_use_gpu(self):
        """Get GPU usage preference"""
        return self.config.get("use_gpu", False)
    
    def set_use_gpu(self, use_gpu):
        """Set GPU usage preference"""
        self.config["use_gpu"] = bool(use_gpu)
    
    def get_multiprocessing(self):
        """Get multiprocessing usage preference"""
        return self.config.get("multiprocessing", True)
    
    def set_multiprocessing(self, use_multiprocessing):
        """Set multiprocessing usage preference"""
        self.config["multiprocessing"] = bool(use_multiprocessing)
    
    def get_max_workers(self):
        """Get maximum worker processes (None = auto-detect)"""
        return self.config.get("max_workers", None)
    
    def set_max_workers(self, max_workers):
        """Set maximum worker processes"""
        if max_workers is None or (isinstance(max_workers, int) and max_workers > 0):
            self.config["max_workers"] = max_workers
            return True
        return False

# Global instance
ocr_config = OCRConfig()