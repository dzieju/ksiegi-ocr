# Kryteria Wyszukiwania - Dokumentacja

## Wprowadzenie
Zakładka "Kryteria wyszukiwania" została pomyślnie przeniesiona i zaimplementowana w repozytorium ksiegi-ocr. Zapewnia kompleksowy interfejs do definiowania, zapisywania i wykonywania zaawansowanych wyszukiwań.

## Struktura plików

### Modele danych
- `models/search_criteria.py` - Główny model danych dla kryteriów wyszukiwania
- `models/__init__.py` - Inicjalizacja pakietu models

### Interfejs graficzny
- `gui/tab_search_criteria.py` - Główna implementacja zakładki GUI
- `gui/main_window.py` - Zaktualizowane o integrację nowej zakładki

### Katalogi
- `search_criteria/` - Domyślny katalog dla przechowywania zapisanych kryteriów

## Funkcjonalności

### 1. Podstawowe parametry wyszukiwania
- Pole tekstowe do wprowadzania zapytania
- Lista rozwijana kategorii (Faktury, Umowy, Korespondencja, etc.)
- Przycisk czyszczenia pól podstawowych

### 2. Zakres dat
- Pola daty "od" i "do"
- Przyciski szybkiego wyboru (ostatni tydzień, miesiąc, 3 miesiące)
- Przycisk czyszczenia dat

### 3. Zakres kwot
- Pola kwoty minimalnej i maksymalnej w PLN
- Walidacja poprawności zakresu

### 4. Opcje wyszukiwania
- Wybór miejsca wyszukiwania (temat, treść, załączniki)
- Opcje zachowania (wielkość liter, całe słowa, załączniki)

### 5. Filtrowanie folderów
- Lista folderów do pominięcia
- Lista folderów do uwzględnienia wyłącznie

### 6. Rozszerzenia plików
- Filtrowanie według rozszerzeń plików
- Przyciski szybkiego wyboru (PDF, DOC, XLS, TXT)

### 7. Zarządzanie kryteriami
- Zapisywanie i wczytywanie zestawów kryteriów
- Eksport i import z plików JSON
- Usuwanie zapisanych zestawów

### 8. Wykonanie wyszukiwania
- Walidacja kryteriów przed wykonaniem
- Wyświetlanie wyników wyszukiwania
- Symulacja wykonania (gotowa do integracji z systemem wyszukiwania)

## Klasy i metody

### SearchCriteria
Główna klasa modelu danych:
- `to_dict()` - Serializacja do słownika
- `from_dict()` - Deserializacja ze słownika
- `save_to_file()` - Zapis do pliku JSON
- `load_from_file()` - Wczytanie z pliku JSON
- `validate()` - Walidacja kryteriów
- `is_empty()` - Sprawdzenie czy kryteria są puste
- `reset()` - Reset do domyślnych wartości

### SearchCriteriaManager
Menedżer zestawów kryteriów:
- `list_saved_criteria()` - Lista zapisanych zestawów
- `save_criteria()` - Zapis zestawu
- `load_criteria()` - Wczytanie zestawu
- `delete_criteria()` - Usunięcie zestawu
- `export_criteria()` - Eksport do pliku
- `import_criteria()` - Import z pliku

### TabSearchCriteria
Główna klasa interfejsu:
- `setup_ui()` - Inicjalizacja interfejsu
- `validate_criteria()` - Walidacja wprowadzonych danych
- `execute_search()` - Wykonanie wyszukiwania
- `reset_all_criteria()` - Reset wszystkich pól
- Metody zarządzania zapisanymi kryteriami

## Integracja

### main_window.py
```python
from gui.tab_search_criteria import TabSearchCriteria

# W konstruktorze MainWindow:
search_criteria_tab = TabSearchCriteria(notebook)
notebook.add(search_criteria_tab, text="Kryteria wyszukiwania")
```

## Walidacja i testy

### Walidacja danych
- Sprawdzanie poprawności zakresów dat
- Sprawdzanie poprawności zakresów kwot
- Walidacja przed wykonaniem wyszukiwania

### Testy integracyjne
Wykonane testy:
- ✅ Import wszystkich modułów
- ✅ Funkcjonalność podstawowa
- ✅ Serializacja/deserializacja
- ✅ Zarządzanie plikami
- ✅ Integracja z główną aplikacją

## Języki i lokalizacja

Interfejs w pełni spolszczony:
- Wszystkie etykiety w języku polskim
- Komunikaty błędów w języku polskim
- Pomoc kontekstowa w języku polskim

## Wymagania systemowe

### Python packages (już zawarte w requirements.txt)
- tkinter (standardowa biblioteka)
- json (standardowa biblioteka)
- datetime (standardowa biblioteka)
- typing (standardowa biblioteka)

### Struktura katalogów
- `models/` - Modele danych
- `search_criteria/` - Przechowywanie zapisanych kryteriów

## Dalszy rozwój

### Możliwe rozszerzenia
1. Integracja z systemem poczty Exchange
2. Integracja z systemem plików
3. Wyszukiwanie w bazach danych
4. Zaawansowane filtry tekstowe (regex)
5. Automatyczne sugestie kryteriów
6. Historia wyszukiwań
7. Raporty z wyników wyszukiwań

### Punkty integracji
Klasa `TabSearchCriteria` zawiera metodę `execute_search()` gotową do rozszerzenia o właściwą logikę wyszukiwania zgodnie z wymaganiami systemu.

## Status implementacji

✅ **UKOŃCZONE** - Wszystkie wymagane funkcjonalności zostały zaimplementowane:
- Pełna funkcjonalność GUI
- Zarządzanie danymi i zapisywanie
- Walidacja i obsługa błędów
- Integracja z główną aplikacją
- Testy i dokumentacja
- Język polski w całym interfejsie

Zakładka "Kryteria wyszukiwania" jest gotowa do użycia i może być rozszerzona o konkretną logikę wyszukiwania według potrzeb projektu.