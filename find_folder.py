def find_folder_by_display_name(account, display_name):
    """
    Znajdź folder na podstawie nazwy wyświetlanej.
    Szukanie nieczułe na wielkość liter, z obsługą polskich i angielskich nazw oraz fragmentów.
    Zwraca obiekt folderu lub None.
    """
    # Zamień na małe litery i usuń spacje
    display_name_clean = display_name.strip().lower()
    # Lista polskich i angielskich synonimów najpopularniejszych folderów
    synonyms = {
        "inbox": ["skrzynka odbiorcza", "inbox"],
        "sent": ["elementy wysłane", "sent items"],
        "drafts": ["wersje robocze", "drafts"],
        "junk": ["wiadomości-śmieci", "junk email", "spam"],
        # Dodaj inne synonimy wg potrzeb
    }
    # Zamień znaną nazwę na listę synonimów (jeśli istnieje)
    candidates = [display_name_clean]
    for names in synonyms.values():
        if display_name_clean in names:
            candidates = names
            break

    # Pierwsze podejście – ścisłe dopasowanie nazwy
    for folder in account.root.walk():
        name = folder.name.strip().lower() if folder.name else ""
        if name in candidates:
            return folder

    # Drugie podejście – czy fragment pasuje do którejś z nazw
    for folder in account.root.walk():
        name = folder.name.strip().lower() if folder.name else ""
        if any(candidate in name for candidate in candidates):
            return folder

    # Ostatecznie wypisz listę dostępnych folderów do debugowania
    print("Dostępne foldery:")
    for folder in account.root.walk():
        print(f"  {folder.absolute} | {repr(folder.name)}")

    print(f"Nie znaleziono folderu o nazwie zbliżonej do: {display_name}")
    return None