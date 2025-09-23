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
    
    def search_emails_threaded(self, connection, search_criteria, page=0, per_page=20):
        """Start threaded email search"""
        self.search_cancelled = False
        
        self.search_thread = threading.Thread(
            target=self._threaded_search,
            args=(connection, search_criteria, page, per_page),
            daemon=True
        )
        self.search_thread.start()
    
    def cancel_search(self):
        """Cancel ongoing search"""
        self.search_cancelled = True
    
    def _threaded_search(self, connection, criteria, page=0, per_page=20):
        """Main search logic running in background thread"""
        try:
            # Get account for folder operations
            account = connection.get_account()
            if not account:
                raise Exception("Nie można nawiązać połączenia z serwerem poczty")
            
            # Get folder path for recursive search
            folder_path = criteria.get('folder_path', 'Skrzynka odbiorcza')
            
            self.progress_callback("Zbieranie folderów do przeszukiwania...")
            
            # Get all folders to search (base folder + all subfolders)
            folders_to_search = connection.get_folder_with_subfolders(account, folder_path)
            
            if not folders_to_search:
                raise Exception("Nie znaleziono folderów do przeszukiwania")
            
            self.progress_callback(f"Przeszukiwanie {len(folders_to_search)} folderów...")
            print(f"Debug: Found {len(folders_to_search)} folders to search")
            
            # Build search query - use simple, reliable approaches
            query_filters = []
            
            # Subject filter - use case-insensitive contains
            if criteria.get('subject_search'):
                # Use subject__contains which is more widely supported than subject__icontains
                subject_filter = Q(subject__contains=criteria['subject_search'])
                query_filters.append(subject_filter)
                print(f"Debug: Added subject filter for: {criteria['subject_search']}")
            
            # Sender filter
            if criteria.get('sender'):
                sender_filter = Q(sender=criteria['sender'])
                query_filters.append(sender_filter)
                print(f"Debug: Added sender filter for: {criteria['sender']}")
            
            # Unread filter
            if criteria.get('unread_only'):
                unread_filter = Q(is_read=False)
                query_filters.append(unread_filter)
                print("Debug: Added unread filter")
            
            # Date period filter
            if criteria.get('selected_period') and criteria['selected_period'] != 'wszystkie':
                start_date = self._get_period_start_date(criteria['selected_period'])
                if start_date:
                    date_filter = Q(datetime_received__gte=start_date)
                    query_filters.append(date_filter)
                    print(f"Debug: Added date filter from: {start_date}")
            
            # Combine filters
            if query_filters:
                combined_query = query_filters[0]
                for query_filter in query_filters[1:]:
                    combined_query &= query_filter
                print(f"Debug: Created combined query with {len(query_filters)} filters")
            else:
                combined_query = None
                print("Debug: No filters applied, will search all messages")
            
            # Search across all folders
            all_messages = []
            for idx, search_folder in enumerate(folders_to_search):
                if self.search_cancelled:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                try:
                    self.progress_callback(f"Przeszukiwanie folderu {idx + 1}/{len(folders_to_search)}: {search_folder.name}")
                    
                    # First try to get some messages without any filtering to test basic functionality
                    if combined_query:
                        print(f"Debug: Applying query filter to folder {search_folder.name}")
                        messages = search_folder.filter(combined_query).order_by('-datetime_received')
                    else:
                        print(f"Debug: Getting all messages from folder {search_folder.name}")
                        messages = search_folder.all().order_by('-datetime_received')
                    
                    # Convert QuerySet to list and limit messages per folder to maintain performance
                    # Use list() on the QuerySet directly instead of slicing first
                    print(f"Debug: Converting messages QuerySet to list for folder {search_folder.name}")
                    try:
                        messages_list = list(messages)
                        print(f"Debug: Successfully converted to list, found {len(messages_list)} messages in folder {search_folder.name}")
                    except Exception as conversion_error:
                        print(f"Debug: Error converting QuerySet to list: {conversion_error}")
                        # Try alternative approach - get first few messages to test
                        try:
                            messages_list = [msg for msg in messages.iterator()]
                            print(f"Debug: Alternative conversion successful, found {len(messages_list)} messages")
                        except Exception as iter_error:
                            print(f"Debug: Iterator approach also failed: {iter_error}")
                            messages_list = []
                    
                    folder_messages = messages_list[:100]  # Limit per folder after converting to list
                    
                    # Add folder information to each message
                    for message in folder_messages:
                        message._search_folder = search_folder  # Store folder reference
                    
                    all_messages.extend(folder_messages)
                    print(f"Debug: Added {len(folder_messages)} messages from folder {search_folder.name}, total so far: {len(all_messages)}")
                    
                except Exception as e:
                    # Log the error but continue with other folders
                    error_msg = f"Błąd w folderze {search_folder.name}: {str(e)}"
                    self.progress_callback(error_msg)
                    print(f"Debug: {error_msg}")
                    import traceback
                    print(f"Debug: Full traceback: {traceback.format_exc()}")
                    continue
            
            # Sort all messages by date
            all_messages.sort(key=lambda m: m.datetime_received if m.datetime_received else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            print(f"Debug: After sorting, have {len(all_messages)} total messages")
            
            self.progress_callback("Przetwarzanie wiadomości...")
            
            # Calculate pagination
            start_idx = page * per_page
            end_idx = start_idx + per_page
            
            # Limit total messages for performance (500 total across all folders)
            total_messages = all_messages[:500]
            total_count = len(total_messages)
            print(f"Debug: Limited to {total_count} messages for processing")
            
            # Filter by attachment criteria if needed  
            filtered_messages = []
            subject_search = criteria.get('subject_search', '').lower() if criteria.get('subject_search') else None
            print(f"Debug: Starting to filter {len(total_messages)} messages. Subject search: {subject_search}")
            
            for message in total_messages:
                if self.search_cancelled:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                try:
                    # Manual subject filtering as backup (case-insensitive)
                    if subject_search:
                        message_subject = (message.subject or '').lower()
                        if subject_search not in message_subject:
                            continue
                    
                    # Check attachment filters if needed
                    if criteria.get('attachments_required') or criteria.get('attachment_name') or criteria.get('attachment_extension'):
                        if not self._check_attachment_filters(message, criteria):
                            continue
                    filtered_messages.append(message)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    print(f"Debug: Error processing message: {e}")
                    continue
            
            print(f"Debug: After filtering, have {len(filtered_messages)} messages")
            
            # Apply pagination to filtered messages
            paginated_messages = filtered_messages[start_idx:end_idx]
            print(f"Debug: After pagination, processing {len(paginated_messages)} messages (page {page}, {start_idx}-{end_idx})")
            
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
                    
                    # Get folder path for this specific message
                    message_folder_path = self._get_folder_path(getattr(message, '_search_folder', None))
                    
                    result_info = {
                        'datetime_received': message.datetime_received,
                        'sender': sender_display,
                        'subject': message.subject if message.subject else 'Brak tematu',
                        'is_read': message.is_read if hasattr(message, 'is_read') else True,
                        'has_attachments': message.has_attachments if hasattr(message, 'has_attachments') else False,
                        'attachment_count': len(message.attachments) if message.attachments else 0,
                        'message_id': message.id if hasattr(message, 'id') else None,
                        'folder_path': message_folder_path,  # Use message-specific folder path
                        'message_obj': message,  # Store full message object for opening
                        'attachments': list(message.attachments) if message.attachments else []
                    }
                    results.append(result_info)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    continue
            
            print(f"Debug: Returning {len(results)} results out of {len(filtered_messages)} filtered messages")
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