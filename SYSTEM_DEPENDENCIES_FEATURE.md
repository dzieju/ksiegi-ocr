# System Dependencies Checklist Feature

## Opis funkcjonalności

Dodano do zakładki System kompletną checklistę zależności środowiskowych z automatycznym sprawdzaniem statusu i emoji jako wskaźnikami. System sprawdza WSZYSTKO co jest wymagane do działania aplikacji KSIEGI-OCR.

## Funkcje

### ✅ Automatyczne sprawdzanie zależności
- **Sprawdzanie na starcie**: Aplikacja automatycznie sprawdza zależności przy uruchomieniu
- **Status w konsoli**: Wyniki wyświetlane w konsoli podczas startu
- **Aktualizacja w tle**: Sprawdzanie odbywa się w osobnym wątku, nie blokując GUI

### 📋 Zakładka "Zależności środowiskowe"
- **Przejrzysta organizacja**: System tab podzielony na 3 zakładki
  - Operacje systemowe
  - **Zależności środowiskowe** (NOWA)
  - Konfiguracja OCR
- **Przewijalna lista**: Wszystkie zależności w przewijalnej liście
- **Przycisk odświeżania**: Możliwość ponownego sprawdzenia w każdej chwili
- **Eksport raportu**: Możliwość wyeksportowania statusu do pliku tekstowego

### 🔍 Sprawdzane zależności

#### Wymagane (REQUIRED) ⚠️:
1. **Python** (3.8+) - ✅ Interpreter Python
2. **Tkinter** - Interfejs graficzny
3. **Tesseract OCR** - Silnik OCR + moduł Python
4. **Poppler** - Narzędzia PDF (pdfinfo, pdfimages, pdftoppm)
5. **pdfplumber** - Ekstrakcja tekstu z PDF
6. **PIL/Pillow** - Przetwarzanie obrazów
7. **OpenCV** - Zaawansowane przetwarzanie obrazów
8. **pdf2image** - Konwersja PDF do obrazów
9. **exchangelib** - Połączenie z Exchange
10. **tkcalendar** - Widget kalendarza
11. **pdfminer.six** - Analiza PDF

#### Opcjonalne (OPTIONAL) 💡:
1. **EasyOCR** - Silnik OCR AI (obsługa GPU)
2. **PaddleOCR** - Silnik OCR AI (obsługa GPU)

### 📊 Statusy i emoji

| Emoji | Status | Znaczenie |
|-------|--------|-----------|
| ✅ | OK | Zależność dostępna i działająca |
| ⚠️ | Warning | Dostępna z ostrzeżeniami lub częściowo |
| ❌ | Error | Zależność niedostępna |

### 💡 Wskazówki instalacji

System automatycznie wyświetla wskazówki instalacji dla brakujących wymaganych zależności:
- **Tkinter**: `apt-get install python3-tk` (Ubuntu/Debian)
- **Tesseract**: `apt-get install tesseract-ocr` (Ubuntu/Debian)
- **Poppler**: `apt-get install poppler-utils` (Ubuntu/Debian)
- **Python moduły**: `pip install [nazwa_modułu]`

## Struktura kodu

### Pliki dodane/zmodyfikowane:

1. **`tools/dependency_checker.py`** (NOWY)
   - Główna klasa `DependencyChecker`
   - Metody sprawdzania różnych typów zależności
   - Interface wiersza poleceń do testowania
   - Funkcje pomocnicze dla łatwego użycia

2. **`gui/system_components/dependency_widget.py`** (NOWY)  
   - Widget GUI dla listy zależności
   - Przewijalna lista z szczegółami
   - Sprawdzanie w tle w osobnym wątku
   - Eksport raportu do pliku

3. **`gui/tab_system.py`** (ZMODYFIKOWANY)
   - Dodano organizację w zakładki (Notebook)
   - Integracja z dependency_widget
   - Zachowanie istniejącej funkcjonalności

4. **`main.py`** (ZMODYFIKOWANY)
   - Integracja sprawdzania zależności przy starcie
   - Wyświetlanie podsumowania w konsoli
   - Ostrzeżenia o brakujących zależnościach

## Rozszerzalność

### 🔧 Dodawanie nowych zależności

Kod został zaprojektowany z myślą o łatwej rozszerzalności:

```python
# W tools/dependency_checker.py, metoda _setup_dependencies()
{
    'name': 'Nazwa zależności',
    'type': 'module',  # lub 'executable', 'system', 'custom', 'executable_and_module'
    'module': 'nazwa_modułu',  # dla type='module'
    'required': True,  # True/False
    'description': 'Opis funkcjonalności'
}
```

### 📝 Typy sprawdzania:
- **`module`**: Sprawdzanie modułów Pythona
- **`executable`**: Sprawdzanie narzędzi w PATH
- **`system`**: Niestandardowe sprawdzanie systemowe
- **`custom`**: Własna funkcja sprawdzająca
- **`executable_and_module`**: Sprawdzanie zarówno programu jak i modułu

## Testowanie

### Wiersz poleceń:
```bash
# Podsumowanie
python tools/dependency_checker.py --summary

# Szczegółowe informacje
python tools/dependency_checker.py --detailed
```

### Przykładowe wyjście:
```
❌ PODSUMOWANIE ZALEŻNOŚCI
========================================
Status: Brak 9 wymaganych zależności
Szczegóły: 2 OK, 0 ostrzeżenia, 11 błędy
⚠️  UWAGA: Brak 9 wymaganych zależności!
```

## Użycie

1. **Uruchom aplikację** - automatyczne sprawdzenie przy starcie
2. **Przejdź do zakładki System** 
3. **Wybierz "Zależności środowiskowe"**
4. **Sprawdź status wszystkich zależności**
5. **Użyj "Odśwież" do ponownego sprawdzenia**
6. **Użyj "Eksportuj" do zapisania raportu**

## Korzyści

- **Diagnostyka problemów**: Łatwe zidentyfikowanie brakujących zależności
- **Wsparcie użytkowników**: Jasne informacje o wymaganiach systemowych  
- **Łatwość utrzymania**: Prosta struktura do dodawania nowych zależności
- **Automatyzacja**: Sprawdzanie bez interwencji użytkownika
- **Dokumentacja**: Eksport statusu do udostępniania przy zgłaszaniu problemów

---

**Status implementacji: ✅ KOMPLETNE**

Wszystkie wymagania z problem statement zostały zrealizowane:
- ✅ Checklista zależności środowiskowych z emoji
- ✅ Sprawdzanie WSZYSTKICH wymaganych komponentów
- ✅ Automatyczne sprawdzanie na starcie
- ✅ Prezentacja w przejrzystej formie w zakładce System
- ✅ Kod łatwy do rozszerzenia o kolejne pozycje