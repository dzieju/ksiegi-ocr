# Dokumentacja: Funkcja "Odczytaj folder"

## Przegląd
Dodano nowy przycisk "Odczytaj folder" w zakładce "Księgi" aplikacji Księgi OCR.

## Lokalizacja
**Zakładka**: Księgi  
**Pozycja**: Trzeci rząd przycisków, pierwsza kolumna

## Funkcjonalność

### Co robi przycisk:
1. **Otwiera dialog wyboru folderu** - użytkownik wskazuje folder na dysku
2. **Skanuje pliki** - odczytuje wszystkie pliki w wybranym folderze (bez podfolderów)
3. **Ekstraktuje nazwy** - pobiera nazwy plików bez rozszerzeń
4. **Tworzy plik CSV** - zapisuje nazwy do pliku CSV w tym samym folderze
5. **Pokazuje wyniki** - wyświetla podsumowanie w obszarze tekstowym

### Szczegóły techniczne:
- **Nazwa pliku CSV**: Identyczna z nazwą folderu (np. `Faktury.csv`)
- **Format CSV**: Jedna nazwa pliku na linię, bez nagłówka
- **Lokalizacja CSV**: Ten sam folder co pliki źródłowe
- **Przetwarzanie**: Tylko pliki w głównym folderze (podfolders są ignorowane)

## Układ interfejsu

```
┌─────────────────────────────────────────────────────────┐
│ Plik PDF (księgi): [______________] [Wybierz plik]      │
│                                                         │
│ [Segmentuj tabelę i OCR] [Pokaż wszystkie komórki OCR] │
│ [OCR z kolumny (wszystkie strony)]                     │
│                                                         │
│ [Odczytaj folder] ←── NOWY PRZYCISK                    │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Text Area - wyniki operacji                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Status: [informacje o operacji]                        │
└─────────────────────────────────────────────────────────┘
```

## Przykład użycia

### Krok 1: Wybór folderu
- Kliknij przycisk "Odczytaj folder"
- Wybierz folder z plikami (np. `C:\Dokumenty\Faktury`)

### Krok 2: Automatyczne przetwarzanie
Jeśli folder zawiera:
```
Faktury/
├── FV_2025_001.pdf
├── FV_2025_002.pdf  
├── faktura_ABC.docx
├── dokument.txt
└── archiwum/           ← ignorowany
    └── stary_plik.pdf  ← ignorowany
```

### Krok 3: Rezultat
Zostanie utworzony plik `Faktury.csv`:
```
FV_2025_001
FV_2025_002
faktura_ABC
dokument
```

### Krok 4: Informacja zwrotna
W obszarze tekstowym pojawi się:
```
Odczytano folder: C:\Dokumenty\Faktury
Znaleziono 4 pliki:

1. FV_2025_001
2. FV_2025_002  
3. faktura_ABC
4. dokument

Plik CSV zapisany jako: C:\Dokumenty\Faktury\Faktury.csv
```

## Obsługa błędów
- **Brak dostępu do folderu**: Komunikat błędu
- **Problemy z zapisem**: Komunikat błędu z detalami
- **Anulowanie wyboru**: Brak akcji, powrót do interfejsu

## Integracja z istniejącym kodem
- **Minimalne zmiany**: Dodano tylko niezbędne elementy
- **Zachowana funkcjonalność**: Wszystkie istniejące funkcje bez zmian
- **Spójny styl**: Używa tych samych komponentów co reszta aplikacji