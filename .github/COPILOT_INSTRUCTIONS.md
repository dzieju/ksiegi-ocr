# Copilot Coding Agent Instructions for dzieju/ksiegi-ocr

## Opis projektu
Repozytorium `ksiegi-ocr` to narzędzie do przetwarzania i wyszukiwania dokumentów oraz maili, głównie dla potrzeb finansowo-księgowych. Projekt obejmuje różne zakładki (funkcjonalności) w GUI, pozwalające m.in. na przeszukiwanie poczty, przetwarzanie dokumentów OCR oraz inne zadania automatyzujące obsługę dokumentów.

## Kluczowe funkcjonalności
- **Przeszukiwanie Poczty**: Zakładka umożliwiająca zaawansowane wyszukiwanie wiadomości e-mail według folderu, tematu, nadawcy, stanu przeczytania, obecności załączników, fragmentu nazwy załącznika oraz jego rozszerzenia.
- **Usuwanie funkcji**: W miarę rozwoju projektu, niepotrzebne zakładki (np. Wyszukiwanie NIP, Odczyt PDF) i związane z nimi pliki są usuwane wraz z wszelkimi odwołaniami w kodzie.
- **Praca na GUI**: Każda funkcjonalność jest realizowana jako osobna zakładka aplikacji. Kod GUI (np. pliki w `gui/`) powinien być spójny i czytelny.

## Zalecane praktyki
- **Każda większa funkcjonalność jako osobna zakładka** w GUI.
- **Usuwanie niepotrzebnych funkcji**: Jeśli polecenie brzmi „usuń zakładkę X”, należy usunąć cały powiązany kod, pliki, testy oraz odwołania.
- **Nazewnictwo**: Nazwy zakładek i pól w interfejsie powinny być po polsku.
- **Wprowadzanie zmian**: Zmiany zgłaszać jako Pull Requesty z wyjaśnieniem co zostało dodane/usunięte.
- **Testy**: Aktualizuj testy po każdej większej zmianie w funkcjonalności.

## Wydajność i UX
- **Wydajność na pierwszym miejscu**: Każda nowa i modyfikowana funkcjonalność musi być tworzona z jak najlepszą wydajnością.
- **Stosowanie multithreadingu/procesów**: Długotrwałe lub obciążające operacje (np. przeszukiwanie, generowanie, odczyt plików) muszą być wykonywane w osobnych wątkach lub procesach, aby GUI nie przestawało odpowiadać i aplikacja nie zawieszała się.
- **Pasek postępu**: Podczas operacji wymagających czasu (np. wyszukiwanie, generowanie raportu, odczyt plików) zawsze pokazuj pasek postępu lub inny wizualny wskaźnik aktualnego stanu realizacji zadania.

- Wszelkie zmiany GUI muszą być czytelne, spójne i zgodne z aktualnym stylem projektu.

## Workflow
1. **Zgłoszenie zadania**: Każda zmiana powinna być zainicjowana przez wyraźne polecenie użytkownika (np. „Dodaj zakładkę X”, „Usuń zakładkę Y”).
2. **Opis PR**: Każdy Pull Request musi jasno opisywać, co zostało zrobione.
3. **Akceptacja**: Zmiany są finalizowane po akceptacji przez użytkownika.

## Inne uwagi
- Kod powinien być zgodny z istniejącą architekturą projektu.
- W razie niejasności – zapytaj użytkownika o doprecyzowanie polecenia.
- Trzymaj się konwencji nazewniczych i stylu kodu obecnych w repozytorium.

---
*Dokument ten służy jako przewodnik dla Copilot Coding Agent oraz innych współpracowników projektu.*