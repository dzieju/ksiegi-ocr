# Email Search Debugging Guide

## Overview
The email search functionality now includes comprehensive logging to help diagnose where results may be lost during the search process. This guide explains what information is logged and how to use it for troubleshooting.

## Where to Find Logs

### Console Output
During search operations, progress messages are displayed both in the GUI and printed to the console with the prefix `[MAIL SEARCH]`.

### Log File
Detailed logs are written to `logs/app.log` with timestamps. You can view logs using:
- The "Pokaż logi" button in the System tab
- By opening the `logs/app.log` file directly

## What Information is Logged

### 1. Search Initialization
```
=== ROZPOCZĘCIE WYSZUKIWANIA EMAIL ===
Parametry wyszukiwania: {'folder_path': 'Skrzynka odbiorcza', 'subject_search': 'faktura', ...}
Paginacja: strona 0, na stronie 20
Połączono z kontem: user@company.com
```

### 2. Folder Discovery
```
=== ODKRYWANIE FOLDERÓW ===
Szukanie folderu bazowego: 'Skrzynka odbiorcza'
Znaleziono folder bazowy: 'Skrzynka odbiorcza'
Rozpoczynanie rekursywnego wyszukiwania podfolderów...
Sprawdzanie podfolderów w: 'Skrzynka odbiorcza'
  Znaleziono podfolder: 'Kompensaty Quadra'
  Znaleziono podfolder: 'Archiwum'
Łącznie folderów do przeszukania: 3
```

### 3. Query Building
```
=== BUDOWANIE ZAPYTANIA WYSZUKIWANIA ===
Dodano filtr tematu: 'faktura'
Dodano filtr nadawcy: 'accounting@company.com'
Utworzono złożone zapytanie z 2 filtrów
```

### 4. Per-Folder Search Results
```
=== PRZESZUKIWANIE FOLDERÓW ===
--- Folder 1/3: 'Skrzynka odbiorcza' ---
Próba zapytania z filtrami dla folderu 'Skrzynka odbiorcza'
Zapytanie z filtrami: znaleziono 15 wiadomości
Folder 'Skrzynka odbiorcza': 15 wiadomości dodano do wyników

--- Folder 2/3: 'Kompensaty Quadra' ---
Próba zapytania z filtrami dla folderu 'Kompensaty Quadra'
BŁĄD zapytania z filtrami: Query not supported
Fallback: pobieranie wszystkich wiadomości z folderu 'Kompensaty Quadra'
Fallback: pobrano 25 wszystkich wiadomości
Folder 'Kompensaty Quadra': 25 wiadomości dodano do wyników
```

### 5. Filtering Statistics
```
=== ETAPY FILTROWANIA ===
Wiadomości przed filtrowaniem: 40
Wyniki filtrowania:
  - Wiadomości po filtrach: 12
  - Odrzucone przez filtr tematu: 25
  - Odrzucone przez filtry załączników: 3
Wiadomości po paginacji: 12
```

### 6. Final Summary
```
=== PODSUMOWANIE WYSZUKIWANIA ===
Całkowita liczba folderów przeszukanych: 3
Wiadomości znalezione ogółem: 40
Wiadomości po limitach i filtrach: 12
Wiadomości na tej stronie: 12
Strona 1 z 1
=== KONIEC WYSZUKIWANIA ===
```

## Common Diagnostic Scenarios

### No Results Found - Troubleshooting Steps

1. **Check Folder Discovery**
   - Look for "BŁĄD: Nie znaleziono folderu bazowego" messages
   - Verify the folder path is correct
   - Check if subfolders are being discovered

2. **Empty Folders**
   - Look for "Folder 'Name': 0 wiadomości dodano do wyników"
   - This indicates the folder exists but contains no messages

3. **Query vs Fallback**
   - If you see "BŁĄD zapytania z filtrami" followed by "Fallback", the Exchange server doesn't support the query
   - Fallback mode retrieves all messages and filters manually (slower but more reliable)

4. **Filtering Issues**
   - Check "Odrzucone przez filtr tematu" count - high numbers indicate overly restrictive subject filters
   - Check "Odrzucone przez filtry załączników" for attachment-related filtering issues

5. **Permissions/Access Issues**
   - Look for "BŁĄD FOLDERU" messages indicating folder access problems
   - Check "BŁĄD dostępu do podfolderów" for subfolder permission issues

### Performance Issues

- **Large Message Counts**: Look for "Ograniczono z X do Y wiadomości" - indicates folder limits being applied
- **Slow Searches**: Check if fallback mode is being used (query failures force slower manual filtering)

## Example Log Analysis

If you're getting fewer results than expected:

1. Find the "PODSUMOWANIE PRZESZUKIWANIA FOLDERÓW" section
2. Check how many messages were found in each folder
3. Look at the "ETAPY FILTROWANIA" section to see where messages were filtered out
4. Review any error messages for specific folders

This logging will help identify whether the issue is:
- Folder access problems
- Empty folders/subfolders  
- Overly restrictive filters
- Server query compatibility issues
- Permission/authentication problems

## Accessing Logs Programmatically

The logging system uses the existing `tools.logger` module:

```python
from tools.logger import read_logs
logs = read_logs()
print(logs)
```