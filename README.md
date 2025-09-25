# KSIEGI-OCR

Projekt GUI do segmentacji tabeli i OCR faktur.

## Opis

Aplikacja pozwala na automatyczne rozpoznawanie tekstu z faktur przy użyciu technologii OCR (Optical Character Recognition). Obsługuje różne silniki OCR w tym Tesseract, EasyOCR i PaddleOCR.

## Stan repozytorium

**To repozytorium zostało przywrócone do stanu po PR #131.**

Cofnięto wszystkie zmiany z PR #132-#136, które wprowadzały:
- Optymalizacje czasu uruchamiania i lazy loading
- Złożone systemy sprawdzania zależności
- Dynamiczne ładowanie zakładek z kompleksową obsługą błędów
- Operacje w tle w wątkach daemon
- Rozbudowane komponenty systemowe i mailowe

Aplikacja została uproszczona do podstawowej, działającej funkcjonalności OCR dla faktur.

## Uruchamianie

```bash
python main.py
```

## Struktura

```
├── gui/
│   ├── main_window.py         # Główne okno aplikacji
│   ├── tab_exchange_config.py # Konfiguracja Exchange
│   └── tab_zakupy.py         # Zakładka do OCR faktur
├── tools/
│   ├── ocr_config.py         # Konfiguracja OCR
│   ├── ocr_engines.py        # Silniki OCR
│   └── logger.py             # System logowania
└── main.py                   # Punkt wejścia aplikacji
```

## Konfiguracja OCR

Aplikacja używa pliku `ocr_config.json` do przechowywania ustawień OCR:

```json
{
  "engine": "tesseract",
  "use_gpu": false,
  "multiprocessing": true,
  "max_workers": null
}
```

## Wymagania

Zobacz `requirements.txt` dla listy zależności Python.

## Funkcjonalność

- **Zakupy**: OCR dla faktur zakupowych
- **Exchange**: Konfiguracja połączenia z serwerem Exchange
- **Podstawowe GUI**: Proste synchroniczne ładowanie zakładek

Złożone funkcje systemowe i przeszukiwania poczty zostały usunięte w ramach przywrócenia stabilnej wersji.

---

**Stan**: Przywrócona wersja po PR #131  
**Usunięte PRs**: #132, #133, #134, #135, #136  
**Kompatybilność**: Python 3.7+, Windows/Linux/macOS