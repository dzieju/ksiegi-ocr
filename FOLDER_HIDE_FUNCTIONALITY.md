# Funkcja ukrywania sekcji wykluczeń folderów

## Przegląd
Zaimplementowana została możliwość ukrywania sekcji "Wyklucz te foldery:" w interfejsie wyszukiwania emaili, wraz z funkcjonalnością zapisywania ustawień.

## Nowe funkcjonalności

### 1. Przycisk "Ukryj/Pokaż"
- Znajduje się obok nagłówka sekcji "Wyklucz te foldery:"
- Pozwala na dynamiczne ukrywanie i pokazywanie checkboxów wyboru folderów
- Tekst przycisku automatycznie zmienia się między "Ukryj" a "Pokaż"

### 2. Przycisk "Zapisz ustawienia"
- Zapisuje aktualnie wybrane foldery do wykluczenia
- Zapisuje stan widoczności sekcji (ukryta/widoczna)
- Wyświetla komunikat potwierdzający zapisanie
- Ustawienia są zapisywane do pliku `mail_search_config.json`

### 3. Automatyczne ładowanie ustawień
- Przy starcie aplikacji automatycznie ładowane są zapisane ustawienia
- Przywracane są wcześniej zaznaczone foldery do wykluczenia
- Przywracany jest stan widoczności sekcji

## Sposób użycia

### Krok 1: Wykrycie folderów
1. Wpisz ścieżkę folderu w polu "Folder przeszukiwania"
2. Kliknij przycisk "Wykryj foldery"
3. Poczekaj na wykrycie dostępnych podfolderów

### Krok 2: Konfiguracja wykluczeń
1. Zaznacz checkboxy przy folderach, które chcesz wykluczyć z wyszukiwania
2. Kliknij "Zapisz ustawienia" aby zachować wybór

### Krok 3: Ukrywanie sekcji (opcjonalne)
1. Kliknij przycisk "Ukryj" aby ukryć sekcję checkboxów
2. Sekcja zostanie schowana, zwalniając miejsce w interfejsie
3. Kliknij "Pokaż" aby ponownie wyświetlić sekcję

### Krok 4: Automatyczne przywracanie
- Po ponownym uruchomieniu aplikacji wszystkie ustawienia zostaną automatycznie przywrócone
- Zaznaczone foldery pozostaną zaznaczone
- Stan widoczności sekcji zostanie zachowany

## Struktura pliku konfiguracyjnego

Plik `mail_search_config.json` zawiera:

```json
{
  "excluded_folders": [
    "Spam",
    "Junk Email", 
    "Newsletter"
  ],
  "exclusion_section_visible": true
}
```

- `excluded_folders`: Lista nazw folderów do wykluczenia
- `exclusion_section_visible`: `true` jeśli sekcja ma być widoczna, `false` jeśli ukryta

## Zmodyfikowane pliki

1. **`gui/mail_search_components/ui_builder.py`**
   - Przepisana metoda `create_folder_exclusion_checkboxes()`
   - Dodano header z przyciskami Ukryj/Pokaż i Zapisz ustawienia

2. **`gui/tab_mail_search.py`**
   - Dodano zarządzanie konfiguracją
   - Dodano metody ładowania/zapisywania ustawień
   - Dodano funkcję ukrywania/pokazywania sekcji

3. **`mail_search_config.json`**
   - Nowy plik konfiguracyjny dla ustawień wyszukiwania

## Kompatybilność
- Funkcjonalność jest w pełni kompatybilna wstecz
- Jeśli plik konfiguracyjny nie istnieje, używane są domyślne ustawienia
- Istniejąca logika wyszukiwania pozostaje niezmieniona