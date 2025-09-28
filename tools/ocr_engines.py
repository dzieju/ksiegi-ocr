"""
OCR engine abstraction with multiprocessing support
"""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import os
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

# Import tesseract utilities for automatic path detection
try:
    from tools.tesseract_utils import get_tesseract_path
    TESSERACT_PATH = get_tesseract_path()
    if TESSERACT_PATH:
        log(f"OCR engines: Tesseract detected at: {TESSERACT_PATH}")
    else:
        log("OCR engines: Warning: Tesseract not detected, using fallback path")
        TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback
except ImportError as e:
    log(f"OCR engines: Failed to import tesseract_utils, using fallback path: {e}")
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback

class OCREngineManager:
    """Manages OCR engines and multiprocessing for OCR operations
    
    Performance Note: On Windows, multiprocessing can sometimes be slower than 
    threading due to process creation overhead. For small batches (< 10 images) 
    or on Windows systems, consider disabling multiprocessing in favor of 
    single-threaded processing or ThreadPoolExecutor for better performance.
    """
    
    def __init__(self):
        self.available_engines = self._detect_available_engines()
        
    def _detect_available_engines(self):
        """Detect which OCR engines are available"""
        engines = {}
        
        # Test Tesseract
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            engines['tesseract'] = True
            log("Tesseract OCR dostępny")
        except ImportError:
            engines['tesseract'] = False
            log("Tesseract OCR niedostępny")
        
        # Test EasyOCR
        try:
            import easyocr
            engines['easyocr'] = True
            log("EasyOCR dostępny")
        except (ImportError, OSError, ValueError) as e:
            engines['easyocr'] = False
            log(f"EasyOCR niedostępny: {e}")
        
        # Test PaddleOCR
        try:
            import paddleocr
            engines['paddleocr'] = True
            log("PaddleOCR dostępny")
        except (ImportError, OSError, ValueError) as e:
            engines['paddleocr'] = False
            log(f"PaddleOCR niedostępny: {e}")
            
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
        """Perform OCR on multiple images with optional multiprocessing
        
        Note: On Windows, multiprocessing overhead can exceed benefits for small batches.
        Consider using single-threaded mode for < 10 images or on Windows systems
        where process creation is expensive.
        """
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
        
        current_engine = self.get_current_engine()
        use_gpu = ocr_config.get_use_gpu()
        
        # Log multiprocessing setup with engine-specific GPU info
        if current_engine == 'tesseract':
            log(f"Uruchamiam multiproces OCR: {max_workers} workerów, silnik: {current_engine} (CPU only - parametr use_gpu zignorowany)")
        else:
            gpu_mode = "GPU" if use_gpu else "CPU"
            log(f"Uruchamiam multiproces OCR: {max_workers} workerów, silnik: {current_engine}, tryb: {gpu_mode}")
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all jobs
                futures = []
                for i, image in enumerate(images):
                    # Prepare arguments based on engine capabilities
                    worker_kwargs = {}
                    
                    # Only pass use_gpu for engines that support it
                    if current_engine in ['easyocr', 'paddleocr']:
                        # Validate use_gpu parameter before passing
                        if not isinstance(use_gpu, bool):
                            log(f"Warning: use_gpu parameter should be boolean, got {type(use_gpu)}: {use_gpu}")
                            worker_kwargs['use_gpu'] = bool(use_gpu)
                        else:
                            worker_kwargs['use_gpu'] = use_gpu
                    elif current_engine == 'tesseract':
                        # Tesseract doesn't support use_gpu, don't pass any parameters
                        if use_gpu:
                            log("Warning: GPU został żądany dla Tesseract, ale nie jest obsługiwany - używam CPU")
                        # worker_kwargs remains empty for tesseract
                    
                    future = executor.submit(_ocr_worker, image, language, current_engine, **worker_kwargs)
                    futures.append(future)
                
                # Collect results
                results = []
                for i, future in enumerate(futures):
                    if progress_callback:
                        progress_callback(i, len(futures))
                    text = future.result()
                    results.append(text)
                
                log(f"Multiproces OCR zakończony pomyślnie, przetworzono {len(results)} obrazów")
                return results
                
        except Exception as e:
            log(f"Błąd wieloprocesowego OCR: {e}, przełączam na tryb pojedynczy")
            # Fallback to single-threaded processing (disable multiprocessing temporarily)
            results = []
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(i, len(images))
                try:
                    text = self.perform_ocr_single(image, language)
                    results.append(text)
                except Exception as single_error:
                    log(f"Błąd pojedynczego OCR dla obrazu {i}: {single_error}")
                    results.append("")  # Empty result for failed image
            return results
    
    def _ocr_tesseract(self, image, language):
        """Perform OCR using Tesseract"""
        import pytesseract
        return pytesseract.image_to_string(image, lang=language)
    
    def _ocr_easyocr_gpu(self, image, language):
        """Perform OCR using EasyOCR with GPU"""
        try:
            import easyocr
            import numpy as np
            
            # Convert PIL image to numpy array
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            reader = easyocr.Reader(['en', 'pl'], gpu=True)
            results = reader.readtext(image)
            
            # Combine all text results
            return '\n'.join([result[1] for result in results])
        except Exception as e:
            log(f"Error in EasyOCR GPU: {e}")
            raise RuntimeError(f"EasyOCR GPU nie jest dostępny: {e}")
    
    def _ocr_easyocr_cpu(self, image, language):
        """Perform OCR using EasyOCR with CPU"""
        try:
            import easyocr
            import numpy as np
            
            # Convert PIL image to numpy array
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            reader = easyocr.Reader(['en', 'pl'], gpu=False)
            results = reader.readtext(image)
            
            # Combine all text results
            return '\n'.join([result[1] for result in results])
        except Exception as e:
            log(f"Error in EasyOCR CPU: {e}")
            raise RuntimeError(f"EasyOCR CPU nie jest dostępny: {e}")
    
    def _ocr_paddleocr_gpu(self, image, language):
        """Perform OCR using PaddleOCR with GPU"""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            
            # Convert PIL image to numpy array
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            # Create OCR instance with GPU enabled, with fallback to CPU
            try:
                ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)
            except Exception as gpu_error:
                log(f"Warning: PaddleOCR GPU initialization failed: {gpu_error}")
                log("Falling back to CPU mode")
                ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
                
            results = ocr.ocr(image, cls=True)
            
            # Extract text from results
            texts = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) > 1:
                        texts.append(line[1][0])
            
            return '\n'.join(texts)
        except Exception as e:
            log(f"Error in PaddleOCR GPU: {e}")
            raise RuntimeError(f"PaddleOCR GPU nie jest dostępny: {e}")
    
    def _ocr_paddleocr_cpu(self, image, language):
        """Perform OCR using PaddleOCR with CPU"""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            
            # Convert PIL image to numpy array
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            # Explicitly create OCR instance with CPU mode
            ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            results = ocr.ocr(image, cls=True)
            
            # Extract text from results
            texts = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) > 1:
                        texts.append(line[1][0])
            
            return '\n'.join(texts)
        except Exception as e:
            log(f"Error in PaddleOCR CPU: {e}")
            raise RuntimeError(f"PaddleOCR CPU nie jest dostępny: {e}")


def _ocr_worker(image, language, engine, **kwargs):
    """Worker function for multiprocessing OCR (must be at module level)"""
    # This function recreates the OCR setup in each worker process
    
    # Extract supported parameters based on engine
    use_gpu = kwargs.get('use_gpu', False)
    
    if engine == 'tesseract':
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # Log warning if GPU parameter was passed for Tesseract
        if 'use_gpu' in kwargs and use_gpu:
            log("Warning: Tesseract nie obsługuje GPU, parametr use_gpu zostanie zignorowany")
        
        # Filter out ALL unsupported arguments for Tesseract (including use_gpu)
        unsupported_args = list(kwargs.keys())
        if unsupported_args:
            log(f"Warning: Nieobsługiwane argumenty dla Tesseract: {unsupported_args}")
        
        return pytesseract.image_to_string(image, lang=language)
    
    elif engine == 'easyocr':
        try:
            import easyocr
            import numpy as np
            
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            # Validate use_gpu parameter
            if not isinstance(use_gpu, bool):
                log(f"Warning: use_gpu musi być boolean, otrzymano {type(use_gpu)}: {use_gpu}")
                use_gpu = bool(use_gpu)
            
            # Log warning for any unsupported arguments (use_gpu is supported)
            unsupported_args = [arg for arg in kwargs.keys() if arg not in ['use_gpu']]
            if unsupported_args:
                log(f"Warning: Nieobsługiwane argumenty dla EasyOCR: {unsupported_args}")
            
            # Create reader with GPU/CPU mode
            try:
                reader = easyocr.Reader(['en', 'pl'], gpu=use_gpu)
            except Exception as reader_error:
                log(f"Error creating EasyOCR reader with gpu={use_gpu}: {reader_error}")
                # Fallback to CPU mode if GPU initialization fails
                if use_gpu:
                    log("Falling back to CPU mode for EasyOCR")
                    reader = easyocr.Reader(['en', 'pl'], gpu=False)
                else:
                    raise
                    
            results = reader.readtext(image)
            return '\n'.join([result[1] for result in results])
        except Exception as e:
            log(f"Error in EasyOCR worker: {e}")
            raise RuntimeError(f"EasyOCR nie jest dostępny: {e}")
    
    elif engine == 'paddleocr':
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            
            if hasattr(image, 'convert'):
                image = np.array(image.convert('RGB'))
            
            # Validate use_gpu parameter
            if not isinstance(use_gpu, bool):
                log(f"Warning: use_gpu musi być boolean, otrzymano {type(use_gpu)}: {use_gpu}")
                use_gpu = bool(use_gpu)
            
            # Log warning for any unsupported arguments (use_gpu is supported)
            unsupported_args = [arg for arg in kwargs.keys() if arg not in ['use_gpu']]
            if unsupported_args:
                log(f"Warning: Nieobsługiwane argumenty dla PaddleOCR: {unsupported_args}")
            
            # Only pass supported arguments to PaddleOCR constructor
            try:
                ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=use_gpu)
            except Exception as constructor_error:
                log(f"Error creating PaddleOCR with use_gpu={use_gpu}: {constructor_error}")
                # Fallback to CPU mode if GPU initialization fails
                if use_gpu:
                    log("Falling back to CPU mode for PaddleOCR")
                    ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
                else:
                    raise
                    
            results = ocr.ocr(image, cls=True)
            
            texts = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) > 1:
                        texts.append(line[1][0])
            
            return '\n'.join(texts)
        except Exception as e:
            log(f"Error in PaddleOCR worker: {e}")
            raise RuntimeError(f"PaddleOCR nie jest dostępny: {e}")
    
    else:
        raise RuntimeError(f"Nieobsługiwany silnik OCR w worker: {engine}")


# Global instance
ocr_manager = OCREngineManager()