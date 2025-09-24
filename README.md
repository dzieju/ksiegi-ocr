# KSIEGI-OCR

System OCR do automatycznego przetwarzania ksiąg i dokumentów PDF z pełną integracją Poppler.

## Funkcjonalności

- **Przetwarzanie PDF**: Automatyczna konwersja i analiza dokumentów PDF
- **OCR (Optical Character Recognition)**: Rozpoznawanie tekstu z obrazów i skanów
- **Integracja Exchange**: Wyszukiwanie i przetwarzanie załączników email
- **Interfejs graficzny**: Intuicyjny GUI oparty na tkinter
- **Lokalna integracja Poppler**: Automatyczne wykrywanie i konfiguracja narzędzi PDF

## Wymagania systemowe

- Python 3.7+
- System operacyjny: Windows, Linux, macOS
- Pamięć RAM: minimum 2GB, zalecane 4GB+
- Miejsce na dysku: minimum 500MB

## Instalacja

### 1. Sklonuj repozytorium

```bash
git clone https://github.com/dzieju/ksiegi-ocr.git
cd ksiegi-ocr
```

### 2. Zainstaluj zależności Python

```bash
pip install -r requirements.txt
```

### 3. Zainstaluj Tesseract OCR

#### Windows
1. Pobierz instalator Tesseract z: [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Zainstaluj Tesseract OCR w domyślnej lokalizacji (`C:\Program Files\Tesseract-OCR\`)
3. Alternatywnie: dodaj `tesseract.exe` do zmiennej środowiskowej PATH

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-pol
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

### 4. Sprawdź integrację Poppler

```bash
python tools/poppler_utils.py --status
```

## Struktura katalogów

```
ksiegi-ocr/
├── main.py                 # Główny punkt wejścia aplikacji
├── gui/                    # Komponenty interfejsu graficznego
│   ├── main_window.py      # Główne okno aplikacji
│   ├── tab_*.py           # Karty interfejsu
│   └── mail_search_components/  # Komponenty wyszukiwania email
├── tools/                  # Narzędzia pomocnicze
│   ├── poppler_utils.py    # Zarządzanie integracją Poppler
│   ├── ocr_engines.py      # Silniki OCR
│   ├── logger.py           # System logowania
│   └── ...
├── poppler/                # Lokalna instalacja Poppler
│   └── Library/
│       └── bin/           # Pliki wykonywalne Poppler (Windows)
├── requirements.txt        # Zależności Python
└── README.md              # Ten plik
```

## Uruchamianie aplikacji

### Podstawowe uruchomienie

```bash
python main.py
```

### Uruchomienie z diagnostyką Poppler

```bash
python tools/poppler_utils.py --status --test
python main.py
```

## Integracja Poppler

### Automatyczne wykrywanie

Aplikacja automatycznie wykrywa i konfiguruje lokalne narzędzia Poppler przy starcie z ulepszoną logiką:

- **Inteligentne wykrywanie ścieżki**: Automatycznie sprawdza następujące lokalizacje w kolejności:
  1. `poppler/Library/bin/` (Windows/conda/vcpkg style)
  2. `poppler/bin/` (Linux/macOS/Unix style)  
  3. `poppler/` (bezpośredni katalog bin)
- **Walidacja narzędzi**: Sprawdza obecność podstawowych plików (`pdfinfo`, `pdfimages`, `pdftoppm`)
- **Automatyczna konfiguracja PATH**: Dodaje wykrytą ścieżkę do zmiennej środowiskowej PATH
- **Elastyczna obsługa**: Działa zarówno z plikami `.exe` (Windows) jak i bez rozszerzenia (Linux/macOS)
- **Sprawdzanie plików PDF**: Automatyczne testy istnienia i dostępności plików PDF przed przetwarzaniem

### Status wykrywania

Sprawdź status wykrywania Poppler:

```bash
python -m tools.poppler_utils --status
```

Przykładowy wynik:
```
==================================================
POPPLER INTEGRATION STATUS
==================================================
Repository root: /path/to/repo
Poppler directory: /path/to/repo/poppler
✓ Poppler DETECTED and CONFIGURED
Bin directory: /path/to/repo/poppler/Library/bin
PATH configured: ✓ Yes

Available tools (12):
  - pdfinfo (pdfinfo.exe)
  - pdfimages (pdfimages.exe)
  - pdftoppm (pdftoppm.exe)
  [...]
==================================================
```

### Dostępne narzędzia Poppler

| Narzędzie | Opis |
|-----------|------|
| `pdfinfo` | Informacje o pliku PDF |
| `pdfimages` | Ekstraktowanie obrazów z PDF |
| `pdftoppm` | Konwersja PDF do obrazów PPM/PNG |
| `pdftotext` | Ekstraktowanie tekstu z PDF |
| `pdftops` | Konwersja PDF do PostScript |
| `pdftohtml` | Konwersja PDF do HTML |
| `pdftocairo` | Renderowanie PDF przez Cairo |
| `pdffonts` | Lista czcionek w PDF |
| `pdfdetach` | Ekstraktowanie załączników |
| `pdfattach` | Dodawanie załączników |
| `pdfseparate` | Rozdzielanie stron PDF |
| `pdfunite` | Łączenie plików PDF |

### Przykłady użycia

#### Programowe wykorzystanie Poppler

```python
from tools.poppler_utils import get_poppler_manager, get_poppler_path

# Uzyskaj instancję managera
manager = get_poppler_manager()

# Sprawdź status
if manager.is_detected:
    print("Poppler jest dostępny!")
    
    # Uzyskaj ścieżkę do narzędzia
    pdfinfo_path = manager.get_tool_path("pdfinfo")
    if pdfinfo_path:
        print(f"pdfinfo znajduje się w: {pdfinfo_path}")
    
    # Testuj narzędzie
    success, message = manager.test_tool("pdfinfo")
    print(f"Test pdfinfo: {message}")

# Szybkie uzyskanie ścieżki poppler (dla bibliotek jak pdf2image)
poppler_path = get_poppler_path()
if poppler_path:
    print(f"Ścieżka Poppler: {poppler_path}")
```

#### Sprawdzanie plików PDF

```python
from tools.poppler_utils import check_pdf_file_exists

# Sprawdź czy plik PDF jest dostępny przed przetwarzaniem
pdf_exists, message = check_pdf_file_exists("dokument.pdf")
if pdf_exists:
    print("Plik PDF jest gotowy do przetwarzania")
    # Kontynuuj z przetwarzaniem...
else:
    print(f"Problem z plikiem PDF: {message}")
```

#### Wykorzystanie w skryptach

```python
import subprocess
from tools.poppler_utils import get_poppler_manager

manager = get_poppler_manager()

# Przykład: uzyskanie informacji o PDF
pdfinfo_path = manager.get_tool_path("pdfinfo")
if pdfinfo_path:
    result = subprocess.run([
        str(pdfinfo_path), 
        "dokument.pdf"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Informacje o PDF:")
        print(result.stdout)
```

#### Konwersja PDF do obrazów

```python
import subprocess
from pathlib import Path
from tools.poppler_utils import get_poppler_manager

def pdf_to_images(pdf_path, output_dir, dpi=300):
    """Konwertuj PDF do obrazów PNG."""
    manager = get_poppler_manager()
    pdftoppm_path = manager.get_tool_path("pdftoppm")
    
    if not pdftoppm_path:
        raise RuntimeError("pdftoppm nie jest dostępne")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Uruchom konwersję
    cmd = [
        str(pdftoppm_path),
        "-png",
        "-r", str(dpi),
        str(pdf_path),
        str(output_dir / "page")
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Błąd konwersji: {result.stderr}")
    
    return list(output_dir.glob("page-*.png"))

# Użycie
try:
    images = pdf_to_images("dokument.pdf", "output_images")
    print(f"Utworzono {len(images)} obrazów")
except Exception as e:
    print(f"Błąd: {e}")
```

## Rozwiązywanie problemów

### Problem: Poppler nie został wykryty

**Objawy:**
```
✗ Poppler NOT DETECTED
Error: Poppler directory not found: /path/to/poppler
```

**Rozwiązania:**
1. Upewnij się, że katalog `poppler` istnieje w katalogu głównym repozytorium
2. Sprawdź strukturę katalogów (obsługiwane są różne struktury):
   ```bash
   ls -la poppler/
   # Opcja 1: Windows/conda style
   ls -la poppler/Library/bin/  
   # Opcja 2: Linux/Unix style  
   ls -la poppler/bin/          
   # Opcja 3: Bezpośredni katalog
   ls -la poppler/              
   ```
3. Uruchom test wykrywania:
   ```bash
   python -m tools.poppler_utils --status
   ```
4. Pobierz i rozpakuj Poppler z oficjalnej strony jeśli katalog nie istnieje

### Problem: Narzędzia Poppler nie działają

**Objawy:**
```
✗ Tool tests failed: pdfinfo: Permission denied
```

**Rozwiązania:**

#### Linux/macOS:
```bash
# Nadaj uprawnienia wykonywania (dla struktury bin/)
chmod +x poppler/bin/*

# Lub dla struktury Library/bin/
chmod +x poppler/Library/bin/*
```

#### Windows:
- Sprawdź, czy pliki `.exe` są obecne w wykrytym katalogu
- Uruchom jako administrator jeśli potrzeba
- Upewnij się, że antywirus nie blokuje plików

### Problem: Nieprawidłowa struktura katalogów

**Objawy:**
```
Error: No valid poppler binaries found in: [PosixPath('/path/to/poppler/Library/bin'), ...]
```

**Rozwiązania:**
1. Sprawdź obecność podstawowych narzędzi:
   ```bash
   # Dla Windows
   ls -la poppler/Library/bin/pdfinfo.exe
   ls -la poppler/Library/bin/pdfimages.exe
   ls -la poppler/Library/bin/pdftoppm.exe
   
   # Dla Linux/macOS
   ls -la poppler/bin/pdfinfo
   ls -la poppler/bin/pdfimages  
   ls -la poppler/bin/pdftoppm
   ```
2. Jeśli brakuje plików, pobierz ponownie Poppler
3. Przetestuj pojedyncze narzędzie:
   ```bash
   python -m tools.poppler_utils --tool pdfinfo
   ```

### Problem: Błędy plików PDF

**Objawy:**
```
PDF file does not exist: /path/to/file.pdf
PDF file appears to be too small (possibly corrupted): /path/to/file.pdf
```

**Rozwiązania:**
1. Sprawdź czy plik istnieje:
   ```bash
   ls -la /path/to/file.pdf
   ```
2. Sprawdź uprawnienia do pliku:
   ```bash
   chmod 644 /path/to/file.pdf
   ```
3. Zweryfikuj integralność pliku PDF:
   ```python
   from tools.poppler_utils import check_pdf_file_exists
   exists, message = check_pdf_file_exists("/path/to/file.pdf")
   print(f"Status: {exists}, Wiadomość: {message}")
   ```

### Problem: Błędy ścieżki PATH

**Objawy:**
```
PATH configured: ✗ No
```

**Rozwiązania:**
1. Uruchom ponownie aplikację - PATH jest konfigurowane automatycznie przy wykryciu Poppler
2. Sprawdź ręcznie status konfiguracji:
   ```python
   from tools.poppler_utils import get_poppler_manager
   manager = get_poppler_manager()
   status = manager.get_status()
   print(f"PATH skonfigurowany: {status['path_configured']}")
   print(f"Ścieżka bin: {status['bin_path']}")
   ```
3. Zweryfikuj czy zmienne środowiskowe są prawidłowe:
   ```bash
   echo $PATH  # Linux/macOS
   echo %PATH% # Windows
   ```

### Problem: Importowanie poppler_utils nie powiodło się

**Objawy:**
```
Failed to import poppler_utils, using fallback path
```

**Rozwiązania:**
1. Sprawdź czy moduł istnieje:
   ```bash
   ls -la tools/poppler_utils.py
   ```
2. Sprawdź ścieżkę Python:
   ```python
   import sys
   print(sys.path)
   ```
3. Uruchom z głównego katalogu repozytorium:
   ```bash
   cd /path/to/ksiegi-ocr
   python -c "from tools.poppler_utils import get_poppler_manager"
   ```

### Problem: Brakujące zależności

**Objawy:**
```bash
ModuleNotFoundError: No module named 'exchangelib'
```

**Rozwiązania:**
```bash
# Zainstaluj wszystkie zależności
pip install -r requirements.txt

# Lub pojedynczo
pip install exchangelib pdfplumber pdf2image pillow
```

### Problem: Błędy OCR

**Objawy:**
- Błędy podczas rozpoznawania tekstu
- Brak wyników OCR
- Komunikat "Tesseract OCR niedostępny"

**Rozwiązania:**
1. Sprawdź instalację Tesseract:
   ```bash
   # Windows
   tesseract --version
   # Linux/macOS
   tesseract --version
   ```

2. Zainstaluj Tesseract jeśli brakuje:
   ```bash
   # Linux (Ubuntu/Debian)
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-pol
   
   # Windows
   # Pobierz z https://github.com/UB-Mannheim/tesseract/wiki
   
   # macOS
   brew install tesseract tesseract-lang
   ```

3. Sprawdź konfigurację OCR w aplikacji:
   ```python
   from tools.ocr_engines import ocr_manager
   print("Available engines:", ocr_manager.get_available_engines())
   print("Current engine:", ocr_manager.get_current_engine())
   ```

4. Sprawdź czy Tesseract jest w PATH:
   ```bash
   # Windows
   where tesseract
   # Linux/macOS
   which tesseract
   ```

### Problem: Błędy GUI

**Objawy:**
```
ModuleNotFoundError: No module named 'tkinter'
```

**Rozwiązania:**

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

#### Windows:
- Tkinter jest zwykle dołączony do Python
- Przeinstaluj Python z opcją "tcl/tk and IDLE"

#### macOS:
```bash
# Z Homebrew
brew install python-tk
```

## Diagnostyka systemu

### Pełna diagnostyka

```bash
# Status Poppler
python tools/poppler_utils.py --status --test

# Test poszczególnych narzędzi
python tools/poppler_utils.py --tool pdfinfo
python tools/poppler_utils.py --tool pdftoppm

# Test OCR
python -c "from tools.ocr_engines import test_ocr_engines; test_ocr_engines()"
```

### Logi diagnostyczne

Aplikacja tworzy pliki logów w katalogu głównym:
- `ocr_log.txt` - logi OCR
- `pdf_error.log` - błędy przetwarzania PDF

### Status pamięci i wydajności

```python
# Sprawdź zużycie pamięci
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Zużycie pamięci: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

## Konfiguracja

### Pliki konfiguracyjne

- `ocr_config.json` - ustawienia OCR
- `exchange_config.json` - konfiguracja Exchange
- `mail_search_config.json` - ustawienia wyszukiwania email

### Przykład konfiguracji OCR

```json
{
  "engine": "tesseract",
  "language": "pol+eng",
  "dpi": 300,
  "preprocessing": true
}
```

## Rozwój i kontrybucje

### Struktura kodu

1. **GUI** (`gui/`) - interfejs użytkownika
2. **Tools** (`tools/`) - narzędzia pomocnicze
3. **OCR** - silniki rozpoznawania tekstu
4. **PDF** - przetwarzanie dokumentów PDF

### Dodawanie nowych funkcji

1. Utwórz moduł w odpowiednim katalogu
2. Dodaj testy w `tests/` (jeśli istnieją)
3. Zaktualizuj dokumentację
4. Stwórz pull request

### Testowanie

```bash
# Test wszystkich komponentów
python -m pytest tests/

# Test konkretnego modułu
python tools/poppler_utils.py --test
```

## Licencja

Ten projekt jest udostępniony na licencji określonej przez właściciela repozytorium.

## Wsparcie

W przypadku problemów:
1. Sprawdź sekcję "Rozwiązywanie problemów"
2. Uruchom pełną diagnostykę
3. Sprawdź logi aplikacji
4. Stwórz issue na GitHub z pełnym opisem problemu

---

**Wersja dokumentacji**: 1.0  
**Ostatnia aktualizacja**: $(date)  
**Kompatybilność**: Python 3.7+, Windows/Linux/macOS