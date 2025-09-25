# Dokumentacja Czytnika EML

## Przegląd

Moduł **Czytnika EML** został dodany do aplikacji Księgi-OCR jako nowa funkcjonalność umożliwiająca przeglądanie plików EML (email) bezpośrednio w aplikacji. Czytnik obsługuje pełne dekodowanie MIME, nagłówki, treść tekstową i HTML, obrazki inline oraz załączniki.

## Lokalizacja

Czytnik EML został zintegrowany z zakładką **"Przeszukiwanie Poczty"** jako nowa podzakładka **"Czytnik EML"**.

### Nawigacja:
1. Główne okno aplikacji
2. Zakładka "Przeszukiwanie Poczty" 
3. Podzakładka "Czytnik EML"

## Funkcjonalności

### 1. Otwieranie plików EML

**Przycisk**: "Otwórz plik EML"

Po kliknięciu przycisku wyświetla się okno dialogowe z wyborem:
- **TAK** - Otwórz w zintegrowanym czytniku (własny podgląd)
- **NIE** - Otwórz w zewnętrznej aplikacji systemowej  
- **ANULUJ** - Nie otwieraj pliku

### 2. Zintegrowany Czytnik

Gdy wybierzesz opcję zintegrowanego czytnika, aplikacja wyświetli treść EML w trzech zakładkach:

#### a) Zakładka "Nagłówki"
- Wyświetla wszystkie nagłówki email
- Automatyczne dekodowanie nagłówków zakodowanych (np. UTF-8, Base64)
- Priorytetowe wyświetlanie najważniejszych nagłówków (Subject, From, To, etc.)
- Pełna lista wszystkich nagłówków

#### b) Zakładka "Treść"
- **Automatyczny wybór**: Preferuje HTML, fallback na tekst
- **Przełącznik typu**: Pozwala wybrać między "auto", "html", "text"
- **Przycisk "Otwórz w przeglądarce"**: Otwiera treść HTML w zewnętrznej przeglądarce
- Obsługa polskich znaków i kodowania UTF-8

#### c) Zakładka "Załączniki"
- Lista wszystkich załączników z informacjami:
  - Nazwa pliku
  - Typ MIME
  - Rozmiar
- **Oznaczenia**: Załączniki inline oznaczone jako "(inline)"
- **Przycisk "Zapisz zaznaczony"**: Zapisuje wybrany załącznik
- **Przycisk "Zapisz wszystkie"**: Zapisuje wszystkie załączniki do wybranego folderu

### 3. Obsługiwane Funkcjonalności MIME

#### Kodowanie
- ✅ UTF-8, ISO-8859-1, Windows-1252
- ✅ Base64, Quoted-Printable
- ✅ 7bit, 8bit

#### Typy zawartości
- ✅ text/plain
- ✅ text/html  
- ✅ multipart/mixed
- ✅ multipart/alternative
- ✅ multipart/related

#### Załączniki
- ✅ Wszystkie typy plików
- ✅ Automatyczne wykrywanie typu MIME
- ✅ Obsługa dużych załączników
- ✅ Załączniki inline (osadzone obrazki)

## Implementacja Techniczna

### Pliki

#### `tools/eml_viewer.py`
Główny moduł zawierający:

**Klasa `EMLReader`**:
- `load_eml_file(filepath)` - wczytuje i parsuje plik EML
- `_extract_headers()` - ekstraktuje i dekoduje nagłówki
- `_extract_body_content()` - ekstraktuje treść tekstową i HTML
- `_extract_attachments()` - ekstraktuje załączniki i treści inline
- `get_preferred_body()` - zwraca preferowaną treść (HTML > tekst)

**Klasa `EMLAttachment`**:
- Przechowuje informacje o załączniku
- `save_to_file(filepath)` - zapisuje załącznik na dysk

**Klasa `EMLViewerGUI`**:
- Interfejs graficzny czytnika
- Zarządzanie zakładkami i widokami
- Obsługa zdarzeń użytkownika

#### `gui/tab_mail_search.py` (zmodyfikowany)
- Dodano strukturę notebook z podzakładkami
- Integracja z EMLViewerGUI
- Zachowanie kompatybilności z istniejącą funkcjonalnością wyszukiwania

## Użycie

### Podstawowe użycie
1. Przejdź do zakładki "Przeszukiwanie Poczty"
2. Kliknij podzakładkę "Czytnik EML"  
3. Kliknij "Otwórz plik EML"
4. Wybierz plik .eml z dysku
5. Wybierz sposób otwarcia (zintegrowany/zewnętrzny)

### Przeglądanie treści
- **Nagłówki**: Sprawdź metadane email
- **Treść**: Przeczytaj wiadomość (HTML lub tekst)
- **Załączniki**: Zapisz załączniki na dysk

### Zapisywanie załączników
1. Przejdź do zakładki "Załączniki"
2. Wybierz załącznik z listy
3. Kliknij "Zapisz zaznaczony" lub "Zapisz wszystkie"
4. Wybierz lokalizację zapisu

## Testowanie

Czytnik został przetestowany z:
- ✅ Prostymi emailami tekstowymi
- ✅ Emailami HTML z formatowaniem
- ✅ Emailami wieloczęściowymi (multipart)
- ✅ Załącznikami różnych typów
- ✅ Kodowaniem polskich znaków
- ✅ Nagłówkami zakodowanymi w Base64

## Rozwiązywanie problemów

### Problem: Błąd dekodowania znaków
**Rozwiązanie**: Czytnik automatycznie używa fallback'u UTF-8 z ignorowaniem błędów

### Problem: Nie można otworzyć zewnętrznej aplikacji
**Rozwiązanie**: Sprawdź czy system ma skonfigurowaną domyślną aplikację dla plików .eml

### Problem: Załącznik nie zapisuje się
**Rozwiązanie**: Sprawdź uprawnienia do zapisu w wybranym folderze

## Kompatybilność

- **System**: Linux, Windows, macOS
- **Python**: 3.6+
- **Zależności**: tkinter, email (standardowe biblioteki)
- **Formaty**: .eml, .msg (częściowo)

## Przyszłe ulepszenia

Planowane funkcjonalności:
- [ ] Podgląd obrazków inline bezpośrednio w aplikacji
- [ ] Eksport do PDF
- [ ] Wyszukiwanie w treści email
- [ ] Historia ostatnio otwieranych plików
- [ ] Obsługa folderów z wieloma plikami EML