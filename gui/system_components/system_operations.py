"""
System operations handler for system functionality  
"""
import threading
from tools import update_checker, email_report


class SystemOperations:
    """Handles system operations like updates and reports in background threads"""
    
    def __init__(self, result_callback):
        self.result_callback = result_callback
        self.operation_cancelled = False
        self.operation_thread = None
    
    def check_update_threaded(self):
        """Start threaded update check"""
        self.operation_cancelled = False
        self.operation_thread = threading.Thread(
            target=self._threaded_check_update,
            daemon=True
        )
        self.operation_thread.start()
    
    def send_report_threaded(self):
        """Start threaded report sending"""
        self.operation_cancelled = False
        self.operation_thread = threading.Thread(
            target=self._threaded_send_report,
            daemon=True
        )
        self.operation_thread.start()
    
    def cancel_operation(self):
        """Cancel ongoing operation"""
        self.operation_cancelled = True
    
    def _threaded_check_update(self):
        """Check for updates in background thread"""
        try:
            if self.operation_cancelled:
                return
            result = update_checker.check_for_update()
            self.result_callback({
                'type': 'update_result',
                'message': result
            })
        except Exception as e:
            self.result_callback({
                'type': 'update_error',
                'error': str(e)
            })
    
    def _threaded_send_report(self):
        """Send report in background thread"""
        try:
            if self.operation_cancelled:
                return
            email_report.send_report()
            self.result_callback({
                'type': 'report_success',
                'message': "Raport wysłany!"
            })
        except Exception as e:
            self.result_callback({
                'type': 'report_error',
                'error': str(e)
            })