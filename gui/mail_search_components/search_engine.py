"""
Email search engine for mail search functionality
"""
import threading
import queue
from datetime import datetime, timedelta, timezone
from tkinter import messagebox
from exchangelib import Q


class EmailSearchEngine:
    """Handles email search operations in background thread"""
    
    def __init__(self, progress_callback, result_callback):
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.search_cancelled = False
        self.search_thread = None
    
    def search_emails_threaded(self, connection, folder, search_criteria):
        """Start threaded email search"""
        self.search_cancelled = False
        
        self.search_thread = threading.Thread(
            target=self._threaded_search,
            args=(connection, folder, search_criteria),
            daemon=True
        )
        self.search_thread.start()
    
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_cancelled = True
    
    def _threaded_search(self, connection, folder, criteria):
        """Main search logic running in background thread"""
        try:
            # Build search query
            query_filters = []
            
            # Subject filter
            if criteria.get('subject'):
                query_filters.append(Q(subject__icontains=criteria['subject']))
            
            # Sender filter
            if criteria.get('sender'):
                query_filters.append(Q(sender=criteria['sender']))
            
            # Unread filter
            if criteria.get('unread_only'):
                query_filters.append(Q(is_read=False))
            
            # Date period filter
            if criteria.get('date_period') and criteria['date_period'] != 'wszystkie':
                start_date = self._get_period_start_date(criteria['date_period'])
                if start_date:
                    query_filters.append(Q(datetime_received__gte=start_date))
            
            # Combine filters
            if query_filters:
                combined_query = query_filters[0]
                for query_filter in query_filters[1:]:
                    combined_query &= query_filter
                    
                messages = folder.filter(combined_query).order_by('-datetime_received')
            else:
                messages = folder.all().order_by('-datetime_received')
            
            self.progress_callback("Przetwarzanie wiadomości...")
            
            results = []
            for i, message in enumerate(messages[:100]):  # Limit to 100 results for performance
                if self.search_cancelled:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                if i % 10 == 0:  # Update progress every 10 messages
                    self.progress_callback(f"Przetworzono {i} wiadomości...")
                
                try:
                    # Check attachment filters if needed
                    if criteria.get('attachments_required') or criteria.get('attachment_name') or criteria.get('attachment_extension'):
                        if not self._check_attachment_filters(message, criteria):
                            continue
                    
                    result_info = {
                        'datetime_received': message.datetime_received,
                        'sender': str(message.sender) if message.sender else 'Nieznany',
                        'subject': message.subject if message.subject else 'Brak tematu',
                        'is_read': message.is_read if hasattr(message, 'is_read') else True,
                        'has_attachments': message.has_attachments if hasattr(message, 'has_attachments') else False,
                        'attachment_count': len(message.attachments) if message.attachments else 0
                    }
                    results.append(result_info)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    continue
            
            self.result_callback({
                'type': 'search_complete',
                'results': results,
                'count': len(results)
            })
            
        except Exception as e:
            self.result_callback({
                'type': 'search_error',
                'error': str(e)
            })
    
    def _get_period_start_date(self, period):
        """Get start date for the selected period"""
        try:
            now = datetime.now(timezone.utc)
            
            if period == "ostatni_tydzien":
                return now - timedelta(days=7)
            elif period == "ostatnie_2_tygodnie":
                return now - timedelta(days=14)
            elif period == "ostatni_miesiac":
                return now - timedelta(days=30)
            elif period == "ostatnie_3_miesiace":
                return now - timedelta(days=90)
            elif period == "ostatnie_6_miesiecy":
                return now - timedelta(days=180)
            elif period == "ostatni_rok":
                return now - timedelta(days=365)
            else:
                return None
        except Exception:
            return None
    
    def _check_attachment_filters(self, message, criteria):
        """Check if message meets attachment criteria"""
        if criteria.get('attachments_required') and not message.has_attachments:
            return False
            
        attachment_name_filter = criteria.get('attachment_name', '').lower()
        attachment_ext_filter = criteria.get('attachment_extension', '').lower()
        
        if not attachment_name_filter and not attachment_ext_filter:
            return True
            
        if not message.attachments:
            return False
            
        for attachment in message.attachments:
            if hasattr(attachment, 'name') and attachment.name:
                attachment_name = attachment.name.lower()
                
                # Check name filter
                if attachment_name_filter and attachment_name_filter not in attachment_name:
                    continue
                    
                # Check extension filter
                if attachment_ext_filter:
                    if not attachment_name.endswith(f'.{attachment_ext_filter}'):
                        continue
                
                # If we get here, attachment matches filters
                return True
        
        return False