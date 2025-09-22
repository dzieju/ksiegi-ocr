"""
Backup operations handler for system functionality
"""
import threading
from tkinter import filedialog, messagebox
from tools import backup


class BackupHandler:
    """Handles backup and restore operations in background threads"""
    
    def __init__(self, result_callback):
        self.result_callback = result_callback
        self.operation_cancelled = False
        self.operation_thread = None
    
    def create_backup_threaded(self):
        """Start threaded backup creation"""
        path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Backup", "*.zip")])
        if path:
            self.operation_cancelled = False
            self.operation_thread = threading.Thread(
                target=self._threaded_create_backup,
                args=(path,),
                daemon=True
            )
            self.operation_thread.start()
            return True
        return False
    
    def restore_backup_threaded(self):
        """Start threaded backup restore"""
        path = filedialog.askopenfilename(filetypes=[("Backup", "*.zip")])
        if path:
            self.operation_cancelled = False
            self.operation_thread = threading.Thread(
                target=self._threaded_restore_backup,
                args=(path,),
                daemon=True
            )
            self.operation_thread.start()
            return True
        return False
    
    def cancel_operation(self):
        """Cancel ongoing operation"""
        self.operation_cancelled = True
    
    def _threaded_create_backup(self, path):
        """Create backup in background thread"""
        try:
            if self.operation_cancelled:
                return
            backup.create_backup(path)
            self.result_callback({
                'type': 'backup_success',
                'message': "Backup utworzony!"
            })
        except Exception as e:
            self.result_callback({
                'type': 'backup_error',
                'error': str(e)
            })
    
    def _threaded_restore_backup(self, path):
        """Restore backup in background thread"""
        try:
            if self.operation_cancelled:
                return
            backup.restore_backup(path)
            self.result_callback({
                'type': 'restore_success',
                'message': "Backup przywrócony!"
            })
        except Exception as e:
            self.result_callback({
                'type': 'restore_error',
                'error': str(e)
            })