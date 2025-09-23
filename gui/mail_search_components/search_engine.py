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
    
    def search_emails_threaded(self, connection, folder, search_criteria, page=0, per_page=20):
        """Start threaded email search"""
        self.search_cancelled = False
        
        self.search_thread = threading.Thread(
            target=self._threaded_search,
            args=(connection, folder, search_criteria, page, per_page),
            daemon=True
        )
        self.search_thread.start()
    
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_cancelled = True
    
    def _threaded_search(self, connection, folder, criteria, page=0, per_page=20):
        """Main search logic running in background thread"""
        try:
            # Get actual folder path from folder object
            folder_path = self._get_folder_path(folder)
            
            # Build search query
            query_filters = []
            
            # Subject filter
            if criteria.get('subject_search'):
                query_filters.append(Q(subject__icontains=criteria['subject_search']))
            
            # Sender filter
            if criteria.get('sender'):
                query_filters.append(Q(sender=criteria['sender']))
            
            # Unread filter
            if criteria.get('unread_only'):
                query_filters.append(Q(is_read=False))
            
            # Date period filter
            if criteria.get('selected_period') and criteria['selected_period'] != 'wszystkie':
                start_date = self._get_period_start_date(criteria['selected_period'])
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
            
            # Calculate pagination
            start_idx = page * per_page
            end_idx = start_idx + per_page
            
            # Get total count (limited to avoid performance issues)
            total_messages = list(messages[:500])  # Limit total to 500 for performance
            total_count = len(total_messages)
            
            # Filter by attachment criteria if needed
            filtered_messages = []
            for message in total_messages:
                if self.search_cancelled:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                try:
                    # Check attachment filters if needed
                    if criteria.get('attachments_required') or criteria.get('attachment_name') or criteria.get('attachment_extension'):
                        if not self._check_attachment_filters(message, criteria):
                            continue
                    filtered_messages.append(message)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    continue
            
            # Apply pagination to filtered messages
            paginated_messages = filtered_messages[start_idx:end_idx]
            
            results = []
            for i, message in enumerate(paginated_messages):
                if self.search_cancelled:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                if i % 5 == 0:  # Update progress every 5 messages
                    self.progress_callback(f"Przetworzono {i + start_idx} wiadomości...")
                
                try:
                    # Extract clean sender email address from Mailbox object
                    sender_display = 'Nieznany'
                    if message.sender:
                        if hasattr(message.sender, 'email_address') and message.sender.email_address:
                            sender_display = message.sender.email_address
                        else:
                            sender_display = str(message.sender)
                    
                    result_info = {
                        'datetime_received': message.datetime_received,
                        'sender': sender_display,
                        'subject': message.subject if message.subject else 'Brak tematu',
                        'is_read': message.is_read if hasattr(message, 'is_read') else True,
                        'has_attachments': message.has_attachments if hasattr(message, 'has_attachments') else False,
                        'attachment_count': len(message.attachments) if message.attachments else 0,
                        'message_id': message.id if hasattr(message, 'id') else None,
                        'folder_path': folder_path,  # Add folder path information
                        'message_obj': message,  # Store full message object for opening
                        'attachments': list(message.attachments) if message.attachments else []
                    }
                    results.append(result_info)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    continue
            
            self.result_callback({
                'type': 'search_complete',
                'results': results,
                'count': len(results),
                'total_count': len(filtered_messages),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(filtered_messages) + per_page - 1) // per_page
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

    def _get_folder_path(self, folder):
        """Get the full folder path from folder object"""
        try:
            if not folder:
                return 'Skrzynka odbiorcza'
            
            # Build path by traversing up the folder hierarchy
            path_parts = []
            current_folder = folder
            is_inbox_child = False
            
            while current_folder and hasattr(current_folder, 'name'):
                folder_name = current_folder.name
                
                # Check if this is an inbox folder
                if folder_name.lower() in ['inbox', 'skrzynka odbiorcza']:
                    # If this is the target folder itself, return inbox name
                    if current_folder == folder:
                        return 'Skrzynka odbiorcza'
                    else:
                        # This is a parent inbox, mark as inbox child
                        is_inbox_child = True
                        break
                
                path_parts.insert(0, folder_name)
                
                # Move to parent folder
                if hasattr(current_folder, 'parent') and current_folder.parent:
                    current_folder = current_folder.parent
                else:
                    break
            
            if not path_parts:
                return 'Skrzynka odbiorcza'
            
            # Create the full path
            if is_inbox_child:
                return '/Odebrane/' + '/'.join(path_parts)
            else:
                return '/' + '/'.join(path_parts)
                
        except Exception as e:
            # Fallback to folder name or generic name
            try:
                return folder.name if hasattr(folder, 'name') else 'Skrzynka odbiorcza'
            except:
                return 'Skrzynka odbiorcza'
    
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