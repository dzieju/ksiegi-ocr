"""
OCR processing utilities for Księgi (book) documents with performance optimizations.
Provides threaded OCR processing similar to PDF attachment processing.
"""
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
import cv2

# Configuration constants
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# OCR region constants for invoice numbers column
CROP_LEFT, CROP_RIGHT = 503, 771
CROP_TOP, CROP_BOTTOM = 332, 2377

# Cell detection parameters
X_MIN = 100
X_MAX = 400

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class OCRTaskManager:
    """Manages threaded OCR operations with progress tracking."""
    
    def __init__(self):
        self.task_cancelled = False
        self.task_executor = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.task_thread = None
    
    def start_task(self, task_function, *args, **kwargs):
        """Start an OCR task in a background thread."""
        self.task_cancelled = False
        self.task_thread = threading.Thread(
            target=task_function,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self.task_thread.start()
        return self.task_thread
    
    def cancel_task(self):
        """Cancel ongoing OCR task."""
        self.task_cancelled = True
        if self.task_executor:
            self.task_executor.shutdown(wait=False)
    
    def is_task_active(self):
        """Check if OCR task is currently running."""
        return self.task_thread and self.task_thread.is_alive()
    
    def get_results(self):
        """Get all available results from the result queue."""
        results = []
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    results.append(result)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników OCR: {e}")
        return results
    
    def get_progress_updates(self):
        """Get all available progress updates from the progress queue."""
        updates = []
        try:
            while True:
                try:
                    progress = self.progress_queue.get_nowait()
                    updates.append(progress)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu OCR: {e}")
        return updates


class KsiegiProcessor:
    """Handles OCR processing for księgi documents with threading support."""
    
    def __init__(self):
        self.task_manager = OCRTaskManager()
    
    def process_pdf_pages_threaded(self, pdf_path, progress_callback=None):
        """
        Process PDF pages with OCR using threading for performance.
        This is the optimized version that processes pages in parallel.
        """
        try:
            # Load all pages first (this is fast)
            self.task_manager.progress_queue.put("Ładowanie stron PDF...")
            images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
            total_pages = len(images)
            
            if total_pages == 0:
                self.task_manager.progress_queue.put("Błąd: Nie znaleziono stron w PDF")
                self.task_manager.result_queue.put({'type': 'task_complete', 'success': False})
                return
            
            self.task_manager.progress_queue.put(f"Przetwarzanie {total_pages} stron...")
            
            # Process pages in parallel using ThreadPoolExecutor
            self._process_pages_parallel(images, total_pages)
            
        except Exception as e:
            print(f"Błąd przetwarzania PDF: {e}")
            self.task_manager.progress_queue.put(f"Błąd: {str(e)}")
            self.task_manager.result_queue.put({'type': 'task_complete', 'success': False, 'error': str(e)})
    
    def _process_pages_parallel(self, images, total_pages):
        """Process PDF pages in parallel using ThreadPoolExecutor."""
        # Use ThreadPoolExecutor for page processing - optimized for I/O bound OCR operations
        max_workers = min(4, total_pages)  # Limit concurrent OCR processes
        self.task_manager.task_executor = ThreadPoolExecutor(max_workers=max_workers)
        
        try:
            # Submit all page processing tasks
            future_to_page = {
                self.task_manager.task_executor.submit(
                    self._process_single_page, page_num, pil_img
                ): page_num
                for page_num, pil_img in enumerate(images, 1)
            }
            
            # Collect results as they complete
            all_lines = []
            processed_count = 0
            
            for future in as_completed(future_to_page):
                if self.task_manager.task_cancelled:
                    break
                    
                processed_count += 1
                page_num = future_to_page[future]
                
                try:
                    result = future.result()
                    if result:
                        # Send page result immediately for real-time feedback
                        self.task_manager.result_queue.put({
                            'type': 'page_complete',
                            'page_num': page_num,
                            'lines': result['lines'],
                            'ocr_text': result['ocr_text']
                        })
                        all_lines.extend(result['lines'])
                    
                    # Update progress
                    self.task_manager.progress_queue.put(
                        f"Ukończono OCR strony {processed_count}/{total_pages}"
                    )
                    
                except Exception as e:
                    print(f"Błąd przetwarzania strony {page_num}: {e}")
                    self.task_manager.progress_queue.put(f"Błąd strony {page_num}: {str(e)}")
            
            # Send final results
            if not self.task_manager.task_cancelled:
                self.task_manager.result_queue.put({
                    'type': 'task_complete',
                    'success': True,
                    'total_lines': len(all_lines),
                    'total_pages': total_pages,
                    'all_lines': all_lines
                })
                self.task_manager.progress_queue.put(
                    f"OCR zakończony: {len(all_lines)} linii z {total_pages} stron"
                )
        
        finally:
            self.task_manager.task_executor.shutdown(wait=True)
            self.task_manager.task_executor = None
    
    def _process_single_page(self, page_num, pil_img):
        """
        Process a single PDF page with OCR.
        This runs in a worker thread for parallel processing.
        """
        try:
            # Crop to the invoice numbers column (performance optimization)
            crop = pil_img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))
            
            # Perform OCR on the cropped region
            ocr_text = pytesseract.image_to_string(crop, lang='pol+eng')
            
            # Extract lines and associate with page number
            lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
            page_lines = [(page_num, line) for line in lines]
            
            return {
                'lines': page_lines,
                'ocr_text': ocr_text,
                'page_num': page_num
            }
            
        except Exception as e:
            print(f"Błąd OCR strony {page_num}: {e}")
            return None
    
    def process_single_page_segmented(self, pil_img):
        """
        Process a single page with cell segmentation.
        Optimized version of the original segmentation logic.
        """
        try:
            # Convert to numpy array for OpenCV processing
            image = np.array(pil_img)
            
            # Detect table cells (optimized with reduced iterations)
            cells = self._detect_table_cells_optimized(image)
            
            # Perform OCR on detected cells (parallel processing within page)
            ocr_results = self._perform_ocr_on_cells_batch(image, cells)
            
            return {
                'cells': cells,
                'ocr_results': ocr_results,
                'image': image
            }
            
        except Exception as e:
            print(f"Błąd segmentacji strony: {e}")
            return None
    
    def _detect_table_cells_optimized(self, image):
        """
        Optimized table cell detection with reduced processing overhead.
        """
        # Convert to grayscale and apply optimized preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blur, 180, 255, cv2.THRESH_BINARY_INV)
        
        # Optimized morphological operations (reduced kernel sizes for speed)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
        
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
        
        # Combine and find contours
        table_mask = cv2.add(vertical_lines, horizontal_lines)
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and sort cells (optimized area threshold)
        cells = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 800]
        cells.sort(key=lambda b: (b[1], b[0]))
        
        return cells
    
    def _perform_ocr_on_cells_batch(self, image, cells):
        """
        Perform OCR on cells with batch processing for better performance.
        """
        results = []
        
        # Process cells in batches to reduce OCR overhead
        batch_size = 10
        for i in range(0, len(cells), batch_size):
            if self.task_manager.task_cancelled:
                break
                
            batch = cells[i:i + batch_size]
            batch_results = []
            
            for (x, y, w, h) in batch:
                # Skip cells outside the target column
                if not (X_MIN <= x <= X_MAX):
                    continue
                
                # Extract ROI and perform OCR
                roi = image[y:y+h, x:x+w]
                text = pytesseract.image_to_string(roi, lang='pol').strip()
                
                # Filter out short texts
                if len(text) >= 5 and self._contains_invoice_number(text):
                    batch_results.append((x, y, text))
            
            results.extend(batch_results)
        
        return results
    
    def _contains_invoice_number(self, text):
        """
        Check if text contains invoice number patterns.
        Reused from original logic but optimized for performance.
        """
        import re
        patterns = [
            r"\bF/\d{5}/\d{2}/\d{2}/M1\b",
            r"\b\d{5}/\d{2}/\d{4}/UP\b", 
            r"\b\d{5}/\d{2}\b",
            r"\b\d{3}/\d{4}\b",
            r"\bF/M\d{2}/\d{7}/\d{2}/\d{2}\b",
            r"\b\d{2}/\d{2}/\d{4}\b",
            r"\b\d{1,2}/\d{2}/\d{4}\b"
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False