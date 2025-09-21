# Księga OCR - Copilot Development Instructions

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Application Overview

Księga OCR is a Python GUI application for processing Polish accounting documents (księgi) using OCR technology. The application features a multi-tab interface built with Tkinter for:
- PDF text extraction and parsing
- Email Exchange server integration for invoice search
- OCR processing of scanned accounting documents
- System configuration and logging

## System Dependencies Setup

**NEVER CANCEL: System installations take 2-5 minutes each. ALWAYS wait for completion.**

### Required System Dependencies
```bash
# Update system packages (30-60 seconds)
sudo apt update

# Install core system dependencies (2-3 minutes) 
sudo apt install -y tesseract-ocr tesseract-ocr-pol poppler-utils python3-tk xvfb

# Verify installations
tesseract --version  # Should show 5.3.4+
pdftoppm -h | head -3  # Should show poppler tools
python3 -c "import tkinter; print('Tkinter available')"  # Should succeed
```

**CRITICAL TIMEOUT SETTINGS:**
- `sudo apt install` commands: Set timeout to 300+ seconds (5+ minutes)
- NEVER CANCEL package installations - they can take several minutes

## Python Environment Setup

### Install Dependencies
```bash
# Install Python dependencies (60-120 seconds)
pip install -r requirements.txt

# Verify key imports work
python3 -c "
import exchangelib, pdfplumber, pytesseract, cv2, pdf2image
from PIL import Image
from tkcalendar import Calendar
print('All dependencies installed successfully')
"
```

**Dependencies in requirements.txt:**
- exchangelib - Exchange server integration
- pdfplumber - PDF text extraction
- pytesseract - OCR text recognition
- opencv-python - Image processing
- pdf2image - PDF to image conversion
- pillow - Image manipulation
- tkcalendar - GUI calendar widgets
- pdfminer.six - PDF parsing support

## Running the Application

### Basic Startup
```bash
# Start with virtual display (for GUI testing)
xvfb-run -a python3 main.py

# Or with timeout for testing (10 seconds is sufficient for startup verification)
timeout 10 xvfb-run -a python3 main.py
```

**Expected startup behavior:**
- GUI initializes successfully
- Loads Exchange configuration (may fail with connection error - expected in sandboxed environments)
- Shows main window with 6 tabs: "Odczyt PDF", "Konfiguracja poczty", "Wyszukiwanie NIP", "Księgi", "Zakupy", "System"

### Application Startup Time
- **Module loading**: ~0.5 seconds
- **GUI initialization**: ~1 second  
- **Full startup with connection attempts**: ~10 seconds

## Processing Performance Expectations

### PDF Text Extraction
- **Simple text extraction**: 2-3 seconds for multi-page document
- **Example**: 108 records from 3-page PDF in 2.2 seconds
- **Timeout recommendation**: 60 seconds for complex documents

### OCR Processing (Most Time-Intensive)
- **Single page OCR**: 3-4 seconds per page
- **Full document OCR**: 8-10 seconds for 3-page document
- **Large documents**: Can take 2-5 minutes for 10+ pages
- **CRITICAL**: NEVER CANCEL OCR operations - Set timeouts to 300+ seconds (5+ minutes)

**OCR Processing Command Example:**
```bash
# NEVER CANCEL: OCR processing takes 2-5 minutes for large documents
timeout 300 python3 -c "from pdf2image import convert_from_path; import pytesseract; print('OCR test')"
```

## Validation Scenarios

### After Making Changes - ALWAYS Run These Tests

1. **Module Import Test** (5 seconds):
```bash
python3 -c "
from gui.main_window import MainWindow
from tools.pdf_parser import extract_pdf_data
from tools.logger import log
print('✓ Core modules import successfully')
"
```

2. **GUI Startup Test** (10 seconds):
```bash
timeout 10 xvfb-run -a python3 main.py
# Expected: GUI starts, shows Exchange connection error (normal), exits after timeout
```

3. **PDF Processing Test** (30 seconds):
```bash
# Test with sample PDF if available
python3 -c "
from tools.pdf_parser import extract_pdf_data
import os
if os.path.exists('KSIEGA 8.pdf'):
    data = extract_pdf_data('KSIEGA 8.pdf')
    print(f'✓ PDF processing works: {len(data)} records extracted')
else:
    print('✓ PDF parser module loads successfully')
"
```

4. **OCR Functionality Test** (60 seconds - NEVER CANCEL):
```bash
timeout 60 python3 -c "
from pdf2image import convert_from_path
import pytesseract
print('✓ OCR dependencies available')
print('Tesseract path:', pytesseract.pytesseract.tesseract_cmd)
"
```

## Repository Structure

### Key Directories
```
/home/runner/work/ksiegi-ocr/ksiegi-ocr/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies  
├── gui/
│   ├── main_window.py        # Main GUI window with tabs
│   ├── tab_pdf_reader.py     # PDF text extraction tab
│   ├── tab_exchange_config.py # Email configuration
│   ├── tab_invoice_search.py # NIP/invoice search
│   ├── tab_ksiegi.py         # Accounting books OCR
│   ├── tab_zakupy.py         # Purchase invoices OCR
│   └── tab_system.py         # System settings
├── tools/
│   ├── pdf_parser.py         # PDF text extraction utilities
│   ├── logger.py             # Application logging
│   ├── update_checker.py     # Version checking
│   └── other utilities...
├── temp_invoices/            # Temporary processing files
└── logs/                     # Application logs
```

### Important Configuration Files
- `exchange_config.json` - Email server settings (contains credentials - in .gitignore)
- `invoice_search_state.json` - UI state persistence
- OCR configuration hardcoded in tab files (Windows paths need adjustment for Linux)

## Processing Results and Output Files

### Generated Files During Operation
- `ocr_log.txt` - OCR processing detailed log with extracted text
- `temp_ocr_table.txt` - Temporary OCR processing results
- `temp_invoice_numbers.txt` - Extracted invoice numbers
- `temp_invoices/` - Directory with temporary PDF downloads
- `logs/app.log` - Application-level logging (auto-created)

### Checking Processing Results
```bash
# View OCR processing log
tail -20 ocr_log.txt

# Check latest application logs  
tail -20 logs/app.log 2>/dev/null || echo "No app logs yet"

# View extracted invoice numbers
head -10 temp_invoice_numbers.txt 2>/dev/null || echo "No invoice numbers extracted yet"

# Check temp processing files
ls -la temp_ocr_*.txt 2>/dev/null || echo "No temp OCR files"
```

### Log File Contents
OCR log format example:
```
=== OCR LOG ===
Timestamp: 2025-09-22 01:38:23
Total pages processed: 5
Total lines: 167

--- RAW OCR OUTPUT ---
Page 1: F/M09/0001895/05/25
Page 1: | 13344/07/2025/UL
Page 1: | 19194/07/2025/UP
```

## Common Development Tasks

### Working with OCR Components
- **OCR settings**: Look for `TESSERACT_PATH` and `POPPLER_PATH` constants in tab files
- **Crop coordinates**: Defined as `CROP_LEFT, CROP_RIGHT, CROP_TOP, CROP_BOTTOM` for precise OCR regions
- **Threading**: OCR operations use background threads - look for `threading` and `queue` imports

### Working with PDF Processing  
- **Text extraction**: Uses `pdfplumber` for direct text extraction
- **Image conversion**: Uses `pdf2image` for OCR preprocessing
- **Processing pipeline**: PDF → Images → Crop → OCR → Text Analysis

### GUI Development
- **Framework**: Tkinter with ttk styling
- **Layout**: Notebook (tabs) with individual Frame classes for each tab
- **Threading**: Long operations use background threads with queue communication

## Platform-Specific Notes

### Linux Environment (Current)
- Tesseract path: `/usr/bin/tesseract` (auto-detected)
- Polish language support: Installed via `tesseract-ocr-pol`
- Poppler tools: Available via `poppler-utils` package

### Windows Paths in Code (Need Adjustment)
The codebase contains Windows-specific paths that need attention:
```python
# Found in tab files - these don't work on Linux:
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Testing and Validation

### Performance Benchmarks
- **Application startup**: <1 second for GUI, ~10 seconds total with connections
- **PDF text extraction**: 2-3 seconds for typical documents
- **OCR processing**: 3-4 seconds per page, up to 5 minutes for large documents
- **Memory usage**: ~90-130MB during OCR processing

### Manual Testing Workflow

#### Complete End-to-End User Scenario (120 seconds)
```bash
# Run this complete test after making changes - NEVER CANCEL
timeout 120 python3 -c "
print('=== COMPLETE END-TO-END TEST ===')
from tools.pdf_parser import extract_pdf_data
from pdf2image import convert_from_path
import pytesseract, time, os

# Test 1: PDF text extraction
if os.path.exists('KSIEGA 8.pdf'):
    start = time.time()
    data = extract_pdf_data('KSIEGA 8.pdf')
    print(f'✓ PDF extraction: {len(data)} records in {time.time()-start:.2f}s')
    
    # Test 2: OCR pipeline
    images = convert_from_path('KSIEGA 8.pdf', dpi=200, first_page=1, last_page=1)
    text = pytesseract.image_to_string(images[0], lang='pol', config='--psm 6')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    print(f'✓ OCR processing: {len(lines)} lines extracted')
    print('✓ All core functionality working')
else:
    print('✓ Core modules load successfully (no test PDF available)')
print('=== TEST COMPLETE ===')
"
```

#### Step-by-Step Validation
1. **Start application**: Verify GUI loads with all 6 tabs
2. **Test PDF tab**: Load a PDF file and verify text extraction
3. **Test OCR tabs** ("Księgi", "Zakupy"): Load PDF and run OCR processing
4. **Check logs**: Verify no critical errors in console output
5. **Verify processing results**: Check that OCR output appears in text areas

### NEVER CANCEL These Operations
- System package installations (`apt install` commands)
- OCR processing (can take 5+ minutes for large documents)
- PDF processing with many pages
- Application builds or dependency installations

**Always set appropriate timeouts: 300+ seconds for OCR, 120+ seconds for builds**

## Common Issues and Solutions

### Missing Dependencies
- **Import errors**: Run the module import test first
- **OCR failures**: Verify tesseract and Polish language data are installed
- **GUI errors**: Ensure python3-tk and xvfb are available
- **"No module named 'tkinter'"**: Install python3-tk package

### Performance Issues
- **Slow OCR**: Expected behavior for large documents - do not cancel
- **Memory usage**: Normal for image processing operations (90-130MB)
- **Network timeouts**: Exchange server connections will fail in sandboxed environments
- **Long processing times**: 3-5 minutes for large PDFs is normal

### Common Error Messages
```bash
# These errors are NORMAL in sandboxed environments:
"Failed to resolve 'ex3.mail.ovh.net'"  # Exchange server not accessible
"HTTPSConnectionPool(...) Max retries"   # Network connection failed
"Błąd ładowania folderów"               # Polish: Error loading folders

# These errors indicate real problems:
"ModuleNotFoundError"                    # Missing Python dependencies
"Error opening data file"                # Missing tesseract language data  
"tesseract: command not found"          # System dependencies missing
```

### Development Best Practices
- **Always test imports**: After modifying any Python file
- **Always run GUI test**: After changing GUI components  
- **Always time OCR operations**: When modifying processing logic
- **Always check logs**: Use `tail ocr_log.txt` to monitor processing
- **Always use proper timeouts**: Never use default timeouts for long operations
- **Always test with real PDFs**: If sample PDFs are available in the repo

REMEMBER: This is a GUI application with intensive OCR processing. Set long timeouts, wait for operations to complete, and always validate functionality after changes.