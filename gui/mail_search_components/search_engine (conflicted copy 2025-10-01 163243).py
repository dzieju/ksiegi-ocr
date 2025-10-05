"""
Email search engine for multi-account mail search
Supports Exchange, IMAP, and POP3 accounts
"""
import threading
import queue
from datetime import datetime, timedelta
from .datetime_utils import IMAPDateHandler
from .pdf_processor import PDFProcessor
from email.header import decode_header
from email.utils import parseaddr

def log(message):
    """Simple logging function"""
    print(f"[SEARCH ENGINE] {message}")

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = ""
    for fragment, charset in decoded_fragments:
        if isinstance(fragment, bytes):
            try:
                result += fragment.decode(charset or "utf-8", errors="replace")
            except Exception:
                result += fragment.decode("utf-8", errors="replace")
        else:
            result += fragment
    return result

def extract_email_address(header_value):
    # Zwraca tylko adres e-mail z nagłówka
    name, email = parseaddr(header_value)
    return email

class EmailSearchEngine:
    """
    Email search engine that handles searching across different mail account types
    """
    
    def __init__(self, progress_callback, result_callback):
        """
        Initialize the search engine
        
        Args:
            progress_callback: Callback function to report progress
            result_callback: Callback function to report results
        """
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.search_thread = None
        self.cancel_flag = False
        self.pdf_history_manager = None
        self.pdf_processor = PDFProcessor()
        
    def search_emails_threaded(self, connection, criteria, page, per_page):
        """
        Start threaded email search
        
        Args:
            connection: MailConnection object
            criteria: Dictionary of search criteria
            page: Current page number (0-indexed)
            per_page: Results per page
        """
        # Cancel any existing search
        if self.search_thread and self.search_thread.is_alive():
            self.cancel_search()
            
        self.cancel_flag = False
        self.search_thread = threading.Thread(
            target=self._threaded_search,
            args=(connection, criteria, page, per_page),
            daemon=True
        )
        self.search_thread.start()
        
    def _threaded_search(self, connection, criteria, page, per_page):
        """
        Perform the actual search in a background thread
        
        Args:
            connection: MailConnection object
            criteria: Dictionary of search criteria
            page: Current page number (0-indexed)
            per_page: Results per page
        """
        try:
            self.progress_callback("Łączenie z serwerem...")
            
            # Get account
            account = connection.get_main_account()
            if not account:
                self.result_callback({'type': 'search_error', 'error': 'Nie znaleziono skonfigurowanego konta'})
                return
                
            account_type = connection.current_account_config.get('type', 'exchange')
            log(f"Searching with account type: {account_type}")
            
            # Get folder
            folder_path = criteria.get('folder_path', 'Skrzynka odbiorcza')
            excluded_folders = criteria.get('excluded_folders', '')
            excluded_folder_list = [f.strip() for f in excluded_folders.split(',') if f.strip()]
            
            self.progress_callback(f"Przeszukiwanie folderu: {folder_path}...")
            
            # Get folder based on account type
            if account_type == 'exchange':
                folder = connection.get_folder_with_subfolders(account, folder_path, excluded_folder_list)
            else:
                folder = connection.get_folder_by_path(account, folder_path)
                
            if not folder:
                self.result_callback({'type': 'search_error', 'error': f'Nie można otworzyć folderu: {folder_path}'})
                return
                
            # Search for messages based on account type
            if account_type == 'exchange':
                messages_list = self._get_exchange_messages(folder, criteria, per_page)
            elif account_type == 'imap_smtp':
                messages_list = self._get_imap_messages(connection, folder, criteria, per_page)
            elif account_type == 'pop3_smtp':
                messages_list = self._get_pop3_messages(folder, criteria, per_page)
            else:
                self.result_callback({'type': 'search_error', 'error': f'Nieobsługiwany typ konta: {account_type}'})
                return
                
            if self.cancel_flag:
                self.result_callback({'type': 'search_cancelled'})
                return
                
            # Apply filters
            filtered_messages = self._filter_messages(messages_list, criteria)
            
            if self.cancel_flag:
                self.result_callback({'type': 'search_cancelled'})
                return
                
            # Calculate pagination
            total_count = len(filtered_messages)
            total_pages = max(1, (total_count + per_page - 1) // per_page)
            start_idx = page * per_page
            end_idx = min(start_idx + per_page, total_count)
            
            # Get current page of results
            paginated_messages = filtered_messages[start_idx:end_idx]
            
            # Convert messages to result format
            results = []
            for msg in paginated_messages:
                if self.cancel_flag:
                    self.result_callback({'type': 'search_cancelled'})
                    return
                    
                result = self._message_to_result(msg, criteria, account_type)
                if result:
                    results.append(result)
                    
            # Return results
            self.result_callback({
                'type': 'search_complete',
                'results': results,
                'count': len(results),
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
            
        except Exception as e:
            log(f"Search error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.result_callback({'type': 'search_error', 'error': str(e)})
            
    def _get_exchange_messages(self, folders, criteria, per_page):
        """
        Get messages from Exchange folder(s)
        
        Args:
            folders: Exchange folder object OR list of folder objects
            criteria: Search criteria
            per_page: Results per page (used for per-folder limit)
            
        Returns:
            List of message objects
        """
        messages_list = []
        from exchangelib import Q
        try:
            # Build filter based on criteria
            query = Q()
            # Date filter
            selected_period = criteria.get('selected_period', 'wszystkie')
            date_range = IMAPDateHandler.get_date_range(selected_period)
            if date_range:
                start_date, end_date = date_range
                query = query & Q(datetime_received__range=(start_date, end_date))
            # Subject filter
            subject_search = criteria.get('subject_search', '')
            if subject_search:
                query = query & Q(subject__icontains=subject_search)
            # Sender filter
            sender = criteria.get('sender', '')
            if sender:
                query = query & Q(sender__icontains=sender)
            # Body filter
            body_search = criteria.get('body_search', '')
            if body_search:
                query = query & Q(body__icontains=body_search)
            # Unread only
            if criteria.get('unread_only', False):
                query = query & Q(is_read=False)
            # Attachments filter
            if criteria.get('attachments_required', False):
                query = query & Q(has_attachments=True)
            elif criteria.get('no_attachments_only', False):
                query = query & Q(has_attachments=False)
            # Execute search
            if isinstance(folders, list):
                for folder in folders:
                    try:
                        messages = folder.filter(query).order_by('-datetime_received')[:per_page]
                        messages_list.extend(list(messages))
                    except Exception as e:
                        log(f"Error searching Exchange folder {folder}: {str(e)}")
            else:
                messages = folders.filter(query).order_by('-datetime_received')[:per_page]
                messages_list = list(messages)
            self.progress_callback(f"Znaleziono {len(messages_list)} wiadomości w folderze Exchange")
        except Exception as e:
            log(f"Error searching Exchange: {str(e)}")
            raise
        return messages_list
        
    def _get_imap_messages(self, connection, folder_name, criteria, per_page):
        """
        Get messages from IMAP folder
        
        Args:
            connection: MailConnection object with imap_connection
            folder_name: IMAP folder name (string)
            criteria: Search criteria
            per_page: Results per page (NOT used for limiting - pagination is at higher level)
            
        Returns:
            List of message objects
        """
        messages_list = []
        
        try:
            folder_name = str(folder_name)
            connection.imap_connection.select_folder(folder_name, readonly=True)
            
            search_criteria = ['ALL']
            
            selected_period = criteria.get('selected_period', 'wszystkie')
            date_range = IMAPDateHandler.get_date_range(selected_period)
            if date_range:
                start_date, end_date = date_range
                if start_date:
                    search_criteria += ['SINCE', start_date.date()]
                if end_date:
                    search_criteria += ['BEFORE', end_date.date()]
            
            subject_search = criteria.get('subject_search', '')
            if subject_search:
                search_criteria.append(f'SUBJECT "{subject_search}"')
            
            sender = criteria.get('sender', '')
            if sender:
                search_criteria.append(f'FROM "{sender}"')
            
            body_search = criteria.get('body_search', '')
            if body_search:
                search_criteria.append(f'BODY "{body_search}"')
            
            if criteria.get('unread_only', False):
                search_criteria.append('UNSEEN')
            
            message_uids = connection.imap_connection.search(search_criteria)
            
            if message_uids:
                fetch_data = connection.imap_connection.fetch(message_uids, ['ENVELOPE', 'FLAGS', 'RFC822.SIZE'])
                
                for uid, data in fetch_data.items():
                    if self.cancel_flag:
                        break
                        
                    envelope = data.get(b'ENVELOPE')
                    flags = data.get(b'FLAGS', [])
                    
                    if envelope:
                        sender_raw = str(envelope.from_[0]) if envelope.from_ else ''
                        msg = {
                            'uid': uid,
                            'subject': decode_mime_header(envelope.subject.decode() if envelope.subject else ''),
                            'sender': extract_email_address(decode_mime_header(sender_raw)),
                            'datetime_received': envelope.date,
                            'is_read': b'\\Seen' in flags,
                            'has_attachments': False,  # Would need to fetch body structure
                            'folder_path': folder_name
                        }
                        messages_list.append(msg)
                        
            self.progress_callback(f"Znaleziono {len(messages_list)} wiadomości w folderze IMAP")
            
        except Exception as e:
            log(f"Error searching IMAP: {str(e)}")
            raise
            
        return messages_list
        
    def _get_pop3_messages(self, folder, criteria, per_page):
        """
        Get messages from POP3 folder
        
        Args:
            folder: POP3 folder connection
            criteria: Search criteria
            per_page: Results per page (used for per-folder limit)
            
        Returns:
            List of message objects
        """
        messages_list = []
        
        try:
            num_messages = len(folder.list()[1])
            limit = min(num_messages, per_page)
            
            for i in range(1, limit + 1):
                if self.cancel_flag:
                    break
                    
                response, lines, octets = folder.retr(i)
                msg_content = b'\n'.join(lines)
                
                from email.parser import BytesParser
                email_message = BytesParser().parsebytes(msg_content)
                subject_raw = email_message.get('Subject', '')
                sender_raw = email_message.get('From', '')
                msg = {
                    'subject': decode_mime_header(subject_raw),
                    'sender': extract_email_address(decode_mime_header(sender_raw)),
                    'datetime_received': datetime.now(),
                    'is_read': True,
                    'has_attachments': False,
                    'folder_path': 'INBOX'
                }
                messages_list.append(msg)
                
            self.progress_callback(f"Pobrano {len(messages_list)} wiadomości z POP3")
            
        except Exception as e:
            log(f"Error fetching POP3 messages: {str(e)}")
            raise
            
        return messages_list
        
    def _filter_messages(self, messages, criteria):
        """
        Apply client-side filters to messages
        
        Args:
            messages: List of message objects
            criteria: Filter criteria
            
        Returns:
            Filtered list of messages
        """
        filtered = []
        
        for msg in messages:
            if self.cancel_flag:
                break
                
            attachment_name = criteria.get('attachment_name', '')
            if attachment_name:
                pass
                
            attachment_extension = criteria.get('attachment_extension', '')
            if attachment_extension:
                pass
                
            pdf_search_text = criteria.get('pdf_search_text', '')
            if pdf_search_text:
                pass
                
            filtered.append(msg)
            
        return filtered
        
    def _message_to_result(self, msg, criteria, account_type):
        """
        Convert message object to result dictionary
        
        Args:
            msg: Message object
            criteria: Search criteria
            account_type: Type of account ('exchange', 'imap_smtp', 'pop3_smtp')
            
        Returns:
            Result dictionary
        """
        try:
            if account_type == 'exchange':
                sender_raw = str(msg.sender) if msg.sender else ''
                result = {
                    'datetime_received': msg.datetime_received,
                    'folder_path': getattr(msg, 'folder', 'Skrzynka odbiorcza'),
                    'sender': extract_email_address(decode_mime_header(sender_raw)),
                    'subject': decode_mime_header(msg.subject or ''),
                    'is_read': msg.is_read,
                    'has_attachments': msg.has_attachments,
                    'attachment_count': len(list(msg.attachments)) if msg.has_attachments else 0,
                    'message_obj': msg,
                    'message_id': msg.message_id if hasattr(msg, 'message_id') else None,
                    'attachments': list(msg.attachments) if msg.has_attachments else []
                }
            else:
                result = {
                    'datetime_received': msg.get('datetime_received', datetime.now()),
                    'folder_path': msg.get('folder_path', 'INBOX'),
                    'sender': msg.get('sender', ''),
                    'subject': decode_mime_header(msg.get('subject', '')),
                    'is_read': msg.get('is_read', True),
                    'has_attachments': msg.get('has_attachments', False),
                    'attachment_count': msg.get('attachment_count', 0),
                    'message_obj': msg,
                    'message_id': msg.get('uid'),
                    'attachments': msg.get('attachments', [])
                }
            return result
            
        except Exception as e:
            log(f"Error converting message to result: {str(e)}")
            return None
            
    def cancel_search(self):
        """Cancel the current search"""
        self.cancel_flag = True
        if self.search_thread:
            self.search_thread.join(timeout=2)