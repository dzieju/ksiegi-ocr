import shutil
import os
import zipfile

BACKUP_ITEMS = ["db.sqlite3", "settings.json", "logs/"]  # Dodaj tu ścieżki plików/katalogów do backupu

def create_backup(backup_path):
    with zipfile.ZipFile(backup_path, 'w') as zipf:
        for item in BACKUP_ITEMS:
            if os.path.exists(item):
                if os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path)
                else:
                    zipf.write(item)
            else:
                print(f"Brak {item} – pomijam...")

def restore_backup(backup_path):
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(".")