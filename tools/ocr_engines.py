"""
OCR engine abstraction with multiprocessing support
"""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
import subprocess
from tools.logger import log
from tools.ocr_config import ocr_config

# Import poppler utilities for automatic path detection
try:
    from tools.poppler_utils import get_poppler_path
    POPPLER_PATH = get_poppler_path()
    if POPPLER_PATH:
        log(f"OCR engines: Poppler detected at: {POPPLER_PATH}")
    else:
        log("OCR engines: Warning: Poppler not detected, using fallback path")
        POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback
except ImportError as e:
    log(f"OCR engines: Failed to import poppler_utils, using fallback path: {e}")
    POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Cache for Tesseract detection to avoid repeated checks
_tesseract_detection_cache = None

def _detect_tesseract():
    """Detect Tesseract OCR availability and provide user feedback"""
    global _tesseract_detection_cache
    
    # Return cached result if available
    if _tesseract_detection_cache is not None:
        return _tesseract_detection_cache
    
    # Try to import pytesseract first
    try:
        import pytesseract
    except ImportError:
        log("Tesseract OCR niedostępny - brak pakietu pytesseract")
        log("Aby zainstalować pytesseract, uruchom: pip install pytesseract")
        _tesseract_detection_cache = (False, None)
        return _tesseract_detection_cache
    
    # Check if tesseract executable is available in PATH
    tesseract_exe = shutil.which('tesseract')
    if tesseract_exe:
        # Test if tesseract works
        try:
            result = subprocess.run([tesseract_exe, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0] if result.stdout else "Tesseract"
                log(f"✓ Tesseract OCR dostępny w systemie PATH: {tesseract_exe}")
                log(f"  Wersja: {version_info}")
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                _tesseract_detection_cache = (True, tesseract_exe)
                return _tesseract_detection_cache
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            log(f"Błąd podczas testowania Tesseract z PATH: {e}")
    
    # Check hardcoded Windows path as fallback
    if os.path.exists(TESSERACT_PATH):
        try:
            result = subprocess.run([TESSERACT_PATH, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0] if result.stdout else "Tesseract"
                log(f"✓ Tesseract OCR dostępny w domyślnej lokalizacji: {TESSERACT_PATH}")
                log(f"  Wersja: {version_info}")
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
                _tesseract_detection_cache = (True, TESSERACT_PATH)
                return _tesseract_detection_cache
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            log(f"Błąd podczas testowania Tesseract z domyślnej ścieżki: {e}")
    
    # Tesseract not found - provide installation instructions
    log("✗ Tesseract OCR niedostępny w systemie")
    log("=" * 60)
    log("INSTRUKCJA INSTALACJI TESSERACT OCR:")
    log("=" * 60)
    log("Windows:")
    log("  1. Pobierz instalator z: https://github.com/UB-Mannheim/tesseract/wiki")
    log("  2. Zainstaluj Tesseract OCR w domyślnej lokalizacji")
    log("  3. Lub dodaj tesseract.exe do zmiennej PATH")
    log("")
    log("Linux (Ubuntu/Debian):")
    log("  sudo apt-get update")
    log("  sudo apt-get install tesseract-ocr tesseract-ocr-pol")
    log("")
    log("macOS:")
    log("  brew install tesseract tesseract-lang")
    log("=" * 60)
    
    _tesseract_detection_cache = (False, None)
    return _tesseract_detection_cache

def clear_tesseract_cache():
    """Clear Tesseract detection cache to force re-detection"""
    global _tesseract_detection_cache
    _tesseract_detection_cache = None

class OCREngineManager:
    """Manages OCR engines and multiprocessing for OCR operations"""
    
    def __init__(self):
        self.available_engines = self._detect_available_engines()
        
    def _detect_available_engines(self):
        """Detect which OCR engines are available"""
        engines = {}
        
        # Test Tesseract with enhanced detection
        tesseract_available, tesseract_path = _detect_tesseract()
        engines['tesseract'] = tesseract_available
        
        # Test EasyOCR
        try:
            import easyocr
            engines['easyocr'] = True
            log("EasyOCR dostępny")
        except ImportError:
            engines['easyocr'] = False
            log("EasyOCR niedostępny")
        
        # Test PaddleOCR
        try:
            import paddleocr
            engines['paddleocr'] = True
            log("PaddleOCR dostępny")
        except ImportError:
            engines['paddleocr'] = False
            log("PaddleOCR niedostępny")
            
        return engines
    
    def get_available_engines(self):
        """Get list of available OCR engines"""
        return [engine for engine, available in self.available_engines.items() if available]
    
    def is_engine_available(self, engine_name):
        """Check if specific engine is available"""
        return self.available_engines.get(engine_name, False)
    
    def get_current_engine(self):
        """Get currently configured engine, falling back to available one if needed"""
        preferred = ocr_config.get_engine()
        
        if self.is_engine_available(preferred):
            return preferred
        
        # Fallback to first available engine
        available = self.get_available_engines()
        if available:
            fallback = available[0]
            log(f"Silnik {preferred} niedostępny, używam {fallback}")
            return fallback
        
        log("Brak dostępnych silników OCR!")
        return None
    
    def perform_ocr_single(self, image, language='pol+eng'):
        """Perform OCR on a single image using configured engine"""
        engine = self.get_current_engine()
        if not engine:
            raise RuntimeError("Brak dostępnych silników OCR")
        
        if engine == 'tesseract':
            return self._ocr_tesseract(image, language)
        elif engine == 'easyocr' and ocr_config.get_use_gpu():
            return self._ocr_easyocr_gpu(image, language)
        elif engine == 'easyocr':
            return self._ocr_easyocr_cpu(image, language)
        elif engine == 'paddleocr' and ocr_config.get_use_gpu():
            return self._ocr_paddleocr_gpu(image, language)
        elif engine == 'paddleocr':
            return self._ocr_paddleocr_cpu(image, language)
        else:
            raise RuntimeError(f"Nieobsługiwany silnik OCR: {engine}")
    
    def perform_ocr_batch(self, images, language='pol+eng', progress_callback=None):
        """Perform OCR on multiple images with optional multiprocessing"""
        if not ocr_config.get_multiprocessing() or len(images) == 1:
            # Single-threaded processing
            results = []
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(i, len(images))
                text = self.perform_ocr_single(image, language)
                results.append(text)
            return results
        
        # Multi-process processing
        max_workers = ocr_config.get_max_workers() or multiprocessing.cpu_count()
        max_workers = min(max_workers, len(images))  # Don't create more workers than images
        
        log(f"Używam {max_workers} procesów dla OCR")
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all jobs
                futures = []
                for i, image in enumerate(images):
                    future = executor.submit(_ocr_worker, image, language, self.get_current_engine(), ocr_config.get_use_gpu())
                    futures.append(future)
                
                # Collect results
                results = []
                for i, future in enumerate(futures):
                    if progress_callback:
                        progress_callback(i, len(futures))
                    text = future.result()
                    results.append(text)
                
                return results
                
        except Exception as e:
            log(f"Błąd wieloprocesowego OCR: {e}, przełączam na tryb pojedynczy")
            # Fallback to single-threaded
            return self.perform_ocr_batch(images, language, progress_callback)
    
    def _ocr_tesseract(self, image, language):
        """Perform OCR using Tesseract"""
        import pytesseract
        return pytesseract.image_to_string(image, lang=language)
    
    def _ocr_easyocr_gpu(self, image, language):
        """Perform OCR using EasyOCR with GPU"""
        import easyocr
        import numpy as np
        
        # Convert PIL image to numpy array
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        reader = easyocr.Reader(['en', 'pl'], gpu=True)
        results = reader.readtext(image)
        
        # Combine all text results
        return '\n'.join([result[1] for result in results])
    
    def _ocr_easyocr_cpu(self, image, language):
        """Perform OCR using EasyOCR with CPU"""
        import easyocr
        import numpy as np
        
        # Convert PIL image to numpy array
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        reader = easyocr.Reader(['en', 'pl'], gpu=False)
        results = reader.readtext(image)
        
        # Combine all text results
        return '\n'.join([result[1] for result in results])
    
    def _ocr_paddleocr_gpu(self, image, language):
        """Perform OCR using PaddleOCR with GPU"""
        from paddleocr import PaddleOCR
        import numpy as np
        
        # Convert PIL image to numpy array
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)
        results = ocr.ocr(image, cls=True)
        
        # Extract text from results
        texts = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1:
                    texts.append(line[1][0])
        
        return '\n'.join(texts)
    
    def _ocr_paddleocr_cpu(self, image, language):
        """Perform OCR using PaddleOCR with CPU"""
        from paddleocr import PaddleOCR
        import numpy as np
        
        # Convert PIL image to numpy array
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
        results = ocr.ocr(image, cls=True)
        
        # Extract text from results
        texts = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1:
                    texts.append(line[1][0])
        
        return '\n'.join(texts)


def _ocr_worker(image, language, engine, use_gpu):
    """Worker function for multiprocessing OCR (must be at module level)"""
    # This function recreates the OCR setup in each worker process
    if engine == 'tesseract':
        import pytesseract
        # Re-detect Tesseract path in worker process
        tesseract_available, tesseract_path = _detect_tesseract()
        if not tesseract_available:
            raise RuntimeError("Tesseract niedostępny w procesie worker")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return pytesseract.image_to_string(image, lang=language)
    
    elif engine == 'easyocr':
        import easyocr
        import numpy as np
        
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        reader = easyocr.Reader(['en', 'pl'], gpu=use_gpu)
        results = reader.readtext(image)
        return '\n'.join([result[1] for result in results])
    
    elif engine == 'paddleocr':
        from paddleocr import PaddleOCR
        import numpy as np
        
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=use_gpu)
        results = ocr.ocr(image, cls=True)
        
        texts = []
        if results and results[0]:
            for line in results[0]:
                if line and len(line) > 1:
                    texts.append(line[1][0])
        
        return '\n'.join(texts)
    
    else:
        raise RuntimeError(f"Nieobsługiwany silnik OCR w worker: {engine}")


# Global instance
ocr_manager = OCREngineManager()