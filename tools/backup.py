import os
import zipfile

def create_backup(backup_path):
    # Katalog główny projektu (tam, gdzie odpalasz aplikację)
    root_dir = os.getcwd()
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(root_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                # Pomijamy plik backupu, żeby nie pętlić
                if os.path.abspath(file_path) == os.path.abspath(backup_path):
                    continue
                arcname = os.path.relpath(file_path, root_dir)
                zipf.write(file_path, arcname)