def list_all_folders(account):
    """
    Wylistuj wszystkie dostępne foldery na koncie Exchange (ścieżka + nazwa).
    """
    for folder in account.root.walk():
        print(f"{folder.absolute} | {repr(folder.name)}")