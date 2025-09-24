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

### 3. Sprawdź integrację Poppler

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

Aplikacja automatycznie wykrywa i konfiguruje lokalne narzędzia Poppler przy starcie:

- **Windows**: `poppler/Library/bin/*.exe`
- **Linux/macOS**: `poppler/bin/*` lub wykrywanie systemowe
- **Konfiguracja PATH**: Automatyczne dodanie do zmiennej środowiskowej PATH

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
from tools.poppler_utils import get_poppler_manager

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
2. Sprawdź strukturę katalogów:
   ```bash
   ls -la poppler/
   ls -la poppler/Library/bin/  # Windows
   ls -la poppler/bin/          # Linux/macOS
   ```
3. Pobierz i rozpakuj Poppler z oficjalnej strony

### Problem: Narzędzia Poppler nie działają

**Objawy:**
```
✗ Tool tests failed: pdfinfo: Permission denied
```

**Rozwiązania:**

#### Linux/macOS:
```bash
# Nadaj uprawnienia wykonywania
chmod +x poppler/bin/*
```

#### Windows:
- Sprawdź, czy pliki `.exe` są obecne w `poppler/Library/bin/`
- Uruchom jako administrator jeśli potrzeba

### Problem: Błędy ścieżki PATH

**Objawy:**
```
PATH configured: ✗ No
```

**Rozwiązania:**
1. Uruchom ponownie aplikację - PATH jest konfigurowane automatycznie
2. Sprawdź ręcznie:
   ```python
   from tools.poppler_utils import get_poppler_manager
   manager = get_poppler_manager()
   print(manager.get_status())
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

**Rozwiązania:**
1. Sprawdź instalację Tesseract:
   ```bash
   # Linux
   sudo apt-get install tesseract-ocr tesseract-ocr-pol
   
   # Windows
   # Pobierz z https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. Sprawdź konfigurację OCR:
   ```python
   from tools.ocr_engines import test_ocr_engines
   test_ocr_engines()
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