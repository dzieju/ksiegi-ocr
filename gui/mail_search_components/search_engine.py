"""
Email search engine for mail search functionality
"""
import threading
import queue
import os
import time
import email
import email.header
import email.utils
import re
from datetime import datetime, timedelta, timezone
from exchangelib import Q, Message
from imapclient import IMAPClient
from tools.logger import log
from .pdf_processor import PDFProcessor
from .datetime_utils import IMAPDateHandler

# Handle optional tkinter import
try:
    from tkinter import messagebox
    HAVE_TKINTER = True
except ImportError:
    HAVE_TKINTER = False
    # Create dummy messagebox for environments without tkinter
    class DummyMessagebox:
        @staticmethod
        def showerror(title, message):
            log(f"Error: {title} - {message}")
    messagebox = DummyMessagebox()


class EmailSearchEngine:
    """Handles email search operations in background thread"""
    
    def __init__(self, progress_callback, result_callback):
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.search_cancelled = False
        self.search_thread = None
        self.pdf_processor = PDFProcessor()
        
        # PDF auto-save support
        self.auto_save_pdfs = False
        self.pdf_save_directory = None
        self.saved_pdf_count = 0
        
        # PDF history manager (will be set by external components)
        self.pdf_history_manager = None
        
        # Cache valid Message field names for validation
        self._valid_fields = self._get_valid_message_fields()
        log(f"Zainicjalizowano wyszukiwarkę z {len(self._valid_fields)} dostępnymi polami Message")
    
    def _is_email_address(self, text):
        """Check if text looks like a complete email address"""
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        # Simple but effective email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, text) is not None
    
    def _get_valid_message_fields(self):
        """Get set of valid field names from exchangelib Message class"""
        try:
            if hasattr(Message, 'FIELDS'):
                # Extract field names from Message.FIELDS
                field_names = set()
                for field in Message.FIELDS:
                    if hasattr(field, 'name'):
                        field_names.add(field.name)
                log(f"Znaleziono {len(field_names)} dostępnych pól w Message.FIELDS")
                return field_names
            else:
                # Fallback to common known fields
                log("OSTRZEŻENIE: Message.FIELDS niedostępne, używam podstawowych pól")
                return {
                    'subject', 'sender', 'datetime_received', 'is_read', 'has_attachments',
                    'attachments', 'datetime_sent', 'datetime_created', 'importance',
                    'to_recipients', 'cc_recipients', 'bcc_recipients'
                }
        except Exception as e:
            log(f"BŁĄD przy pobieraniu pól Message: {str(e)}, używam podstawowych pól")
            return {
                'subject', 'sender', 'datetime_received', 'is_read', 'has_attachments'
            }
    
    def _validate_and_log_filter(self, field_name, field_value, filter_obj):
        """Validate field and log filter creation"""
        log(f"Tworzenie filtru: {field_name} = '{field_value}'")
        
        if field_name not in self._valid_fields:
            log(f"OSTRZEŻENIE: Pole '{field_name}' nie istnieje w Message.FIELDS!")
            log(f"Dostępne pola Message obejmują: {', '.join(sorted(list(self._valid_fields)[:10]))}...")
            if len(self._valid_fields) > 10:
                log(f"Oraz {len(self._valid_fields) - 10} dodatkowych pól. Pełna lista w logach inicjalizacji.")
            
            # Suggest alternatives for common mistakes
            if field_name == 'folder_path':
                log("PORADA: folder_path to kryterium UI, nie pole Message. Użyj subject/sender/datetime_received dla filtrowania.")
            elif field_name.startswith('_'):
                log("PORADA: Pola rozpoczynające się od '_' nie są prawidłowymi polami Message.")
            
            return False
        
        log(f"✓ Pole '{field_name}' zweryfikowane jako prawidłowe pole Message")
        return True
    
    def _create_safe_filter(self, field_name, field_value, lookup_type='exact'):
        """Create Q filter with validation and logging"""
        if not self._validate_and_log_filter(field_name, field_value, None):
            log(f"POMINIĘCIE nieprawidłowego filtru: {field_name}")
            return None
        
        try:
            if lookup_type == 'contains':
                filter_dict = {f"{field_name}__contains": field_value}
            elif lookup_type == 'icontains':
                # Case-insensitive contains
                filter_dict = {f"{field_name}__icontains": field_value}
            elif lookup_type == 'gte':
                filter_dict = {f"{field_name}__gte": field_value}
            else:
                filter_dict = {field_name: field_value}
            
            q_filter = Q(**filter_dict)
            log(f"Utworzono filtr Q({field_name}__{lookup_type if lookup_type != 'exact' else ''}={field_value})")
            return q_filter
        except Exception as e:
            log(f"BŁĄD tworzenia filtru Q({field_name}={field_value}): {str(e)}")
            return None
    
    def search_emails_threaded(self, connection, search_criteria, page=0, per_page=500):
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
        self.pdf_processor.cancel_search()
    
    def _threaded_search(self, connection, criteria, page=0, per_page=500):
        """Main search logic running in background thread"""
        try:
            # Log search start
            search_params = {k: v for k, v in criteria.items() if k != 'password'}  # Exclude sensitive data
            log(f"=== ROZPOCZĘCIE WYSZUKIWANIA EMAIL ===")
            log(f"Parametry wyszukiwania: {search_params}")
            log(f"Paginacja: strona {page}, na stronie {per_page}")
            
            # Get account for folder operations and determine account type
            account = connection.get_main_account()
            if not account:
                log("BŁĄD: Nie można nawiązać połączenia z serwerem poczty")
                raise Exception("Nie można nawiązać połączenia z serwerem poczty")
            
            # Determine account type for universal handling
            account_type = "unknown"
            if connection.current_account_config:
                account_type = connection.current_account_config.get("type", "unknown")
            else:
                # Try to detect account type from account object
                if hasattr(account, 'primary_smtp_address'):
                    account_type = "exchange"
                else:
                    account_type = "imap_smtp"  # Default for non-Exchange
            
            log(f"Detected account type: {account_type}")
            
            # Enhanced account and folder context logging
            if connection.current_account_config:
                account_name = connection.current_account_config.get("name", "Unknown")
                account_email = connection.current_account_config.get("email", "Unknown")
                log(f"=== KONTEKST WYSZUKIWANIA ===")
                log(f"Konto: '{account_name}' ({account_email})")
                log(f"Typ konta: {account_type}")
                
                # Show folder mapping for IMAP/POP accounts
                folder_path = criteria.get('folder_path', 'Skrzynka odbiorcza')
                if account_type in ["imap_smtp", "pop3_smtp"]:
                    from gui.mail_search_components.mail_connection import FolderNameMapper
                    server_folder = FolderNameMapper.polish_to_server(folder_path)
                    if server_folder != folder_path:
                        log(f"Folder wyszukiwania: '{folder_path}' → '{server_folder}'")
                    else:
                        log(f"Folder wyszukiwania: '{folder_path}'")
                else:
                    log(f"Folder wyszukiwania: '{folder_path}'")
                log("=" * 30)
            
            # Log connection info (works for both Exchange and IMAP)
            if hasattr(account, 'primary_smtp_address'):
                log(f"Połączono z kontem Exchange: {account.primary_smtp_address}")
            else:
                # For IMAP connections, we need to get the email from connection config
                config = connection.current_account_config
                if config:
                    log(f"Połączono z kontem IMAP: {config.get('email', 'Unknown')}")
                else:
                    log("Połączono z kontem pocztowym")
            
            # Get folder path for recursive search
            folder_path = criteria.get('folder_path', 'Skrzynka odbiorcza')
            excluded_folders = criteria.get('excluded_folders', '')
            log(f"Ścieżka bazowego folderu: '{folder_path}'")
            if excluded_folders:
                log(f"Foldery do wykluczenia: '{excluded_folders}'")
            
            self.progress_callback("Zbieranie folderów do przeszukiwania...")
            
            # Get all folders to search (base folder + all subfolders)
            folders_to_search = connection.get_folder_with_subfolders(account, folder_path, excluded_folders)
            
            if not folders_to_search:
                log("BŁĄD: Nie znaleziono folderów do przeszukiwania")
                raise Exception("Nie znaleziono folderów do przeszukiwania")
            
            log(f"Znaleziono {len(folders_to_search)} folderów do przeszukiwania:")
            for i, folder in enumerate(folders_to_search, 1):
                log(f"  {i}. {self._get_safe_folder_name(folder)}")
            
            self.progress_callback(f"Przeszukiwanie {len(folders_to_search)} folderów...")
            
            # Build search query - use safe, validated approaches
            log("=== BUDOWANIE ZAPYTANIA WYSZUKIWANIA ===")
            query_filters = []
            
            # Subject filter - use case-insensitive contains
            if criteria.get('subject_search'):
                subject_filter = self._create_safe_filter('subject', criteria['subject_search'], 'icontains')
                if subject_filter:
                    query_filters.append(subject_filter)
                    log(f"Dodano filtr tematu (case-insensitive): '{criteria['subject_search']}'")
                else:
                    log(f"POMINIĘTO nieprawidłowy filtr tematu")
            
            # Body filter - use case-insensitive contains
            if criteria.get('body_search'):
                body_filter = self._create_safe_filter('body', criteria['body_search'], 'icontains')
                if body_filter:
                    query_filters.append(body_filter)
                    log(f"Dodano filtr treści (case-insensitive): '{criteria['body_search']}'")
                else:
                    log(f"POMINIĘTO nieprawidłowy filtr treści")
            
            # Sender filter - use IMAP FROM filter only for full email addresses
            if criteria.get('sender'):
                sender_value = criteria['sender']
                if self._is_email_address(sender_value):
                    # Full email address - use Exchange query filter
                    sender_filter = self._create_safe_filter('sender', sender_value, 'icontains')
                    if sender_filter:
                        query_filters.append(sender_filter)
                        log(f"Dodano filtr nadawcy Exchange (full email): '{sender_value}'")
                    else:
                        log(f"POMINIĘTO nieprawidłowy filtr nadawcy")
                else:
                    # Fragment - skip Exchange filter, will filter locally later
                    log(f"Fragment nadawcy wykryty: '{sender_value}' - zostanie zastosowany lokalny filtr")
            
            # Unread filter
            if criteria.get('unread_only'):
                unread_filter = self._create_safe_filter('is_read', False)
                if unread_filter:
                    query_filters.append(unread_filter)
                    log("Dodano filtr nieprzeczytanych wiadomości")
                else:
                    log("POMINIĘTO nieprawidłowy filtr nieprzeczytanych wiadomości")
            
            # Date period filter
            if criteria.get('selected_period') and criteria['selected_period'] != 'wszystkie':
                start_date = self._get_period_start_date(criteria['selected_period'])
                if start_date:
                    date_filter = self._create_safe_filter('datetime_received', start_date, 'gte')
                    if date_filter:
                        query_filters.append(date_filter)
                        log(f"Dodano filtr daty: od {start_date} (okres: {criteria['selected_period']})")
                    else:
                        log(f"POMINIĘTO nieprawidłowy filtr daty")
            
            # Log all created filters
            log(f"=== PODSUMOWANIE FILTRÓW ===")
            for i, filter_obj in enumerate(query_filters, 1):
                log(f"Filtr {i}: {filter_obj}")
            
            # Check for and warn about any invalid field attempts
            log("=== WALIDACJA KRYTERIÓW WYSZUKIWANIA ===")
            invalid_field_warnings = []
            valid_field_count = 0
            
            for key, value in criteria.items():
                if key.startswith('_'):
                    invalid_field_warnings.append(f"OSTRZEŻENIE: Wykryto nieprawidłowe pole prywatne w kryteriach: '{key}'")
                    if key == '_search_folder':
                        invalid_field_warnings.append("  └── '_search_folder' nie jest prawidłowym polem Message. Użyj 'folder_path' zamiast tego.")
                    elif key == '_folder_reference':
                        invalid_field_warnings.append("  └── '_folder_reference' nie jest prawidłowym polem Message. Foldery są określane przez folder_path.")
                    else:
                        invalid_field_warnings.append(f"  └── Pola rozpoczynające się od '_' nie powinny być używane w filtrach wiadomości.")
                elif key in ['folder_path', 'excluded_folders', 'subject_search', 'pdf_search_text', 'sender', 'unread_only', 'attachments_required', 
                           'attachment_name', 'attachment_extension', 'selected_period']:
                    # These are valid UI/search criteria (not Message fields)
                    valid_field_count += 1
                elif key in self._valid_fields:
                    # These are valid Message fields
                    valid_field_count += 1
                    log(f"✓ Pole '{key}' zweryfikowane jako prawidłowe pole Message")
                else:
                    # This might be an invalid field
                    invalid_field_warnings.append(f"OSTRZEŻENIE: Pole '{key}' nie zostało znalezione w Message.FIELDS!")
                    invalid_field_warnings.append(f"  └── Dostępne pola Message: {', '.join(sorted(list(self._valid_fields)[:15]))}...")
                    if len(self._valid_fields) > 15:
                        invalid_field_warnings.append(f"  └── I {len(self._valid_fields) - 15} więcej pól...")
            
            # Log all validation warnings
            if invalid_field_warnings:
                log(f"Znaleziono {len(invalid_field_warnings)} ostrzeżeń walidacyjnych:")
                for warning in invalid_field_warnings:
                    log(warning)
            else:
                log("✓ Wszystkie pola w kryteriach wyszukiwania są prawidłowe")
            
            log(f"Podsumowanie walidacji: {valid_field_count} prawidłowych pól, {len(invalid_field_warnings)} ostrzeżeń")
            
            # Log which criteria will be used for filtering
            valid_criteria_count = 0
            if criteria.get('subject_search'):
                log(f"✓ Używam filtru tematu: '{criteria['subject_search']}'")
                valid_criteria_count += 1
            if criteria.get('sender'):
                log(f"✓ Używam filtru nadawcy: '{criteria['sender']}'")
                valid_criteria_count += 1
            if criteria.get('pdf_search_text'):
                log(f"✓ Używam wyszukiwania w PDF: '{criteria['pdf_search_text']}'")
                valid_criteria_count += 1
            if criteria.get('unread_only'):
                log("✓ Używam filtru nieprzeczytanych wiadomości")
                valid_criteria_count += 1
            if criteria.get('selected_period') and criteria['selected_period'] != 'wszystkie':
                log(f"✓ Używam filtru okresu: '{criteria['selected_period']}'")
                valid_criteria_count += 1
                
            log(f"Łącznie prawidłowych kryteriów filtrowania: {valid_criteria_count}")
            
            # Combine filters
            if query_filters:
                combined_query = query_filters[0]
                for query_filter in query_filters[1:]:
                    combined_query &= query_filter
                log(f"Utworzono złożone zapytanie z {len(query_filters)} prawidłowych filtrów")
            else:
                combined_query = None
                log("Brak prawidłowych filtrów - pobieranie wszystkich wiadomości")
            
            # Search across all folders
            log("=== PRZESZUKIWANIE FOLDERÓW ===")
            all_messages = []
            folder_results = {}  # Track results per folder
            message_to_folder_map = {}  # Map message IDs to their folder paths (avoid modifying message objects)
            
            for idx, search_folder in enumerate(folders_to_search):
                if self.search_cancelled:
                    log("Wyszukiwanie anulowane przez użytkownika")
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                folder_name = self._get_safe_folder_name(search_folder)
                log(f"--- Folder {idx + 1}/{len(folders_to_search)}: '{folder_name}' ---")
                
                try:
                    self.progress_callback(f"Przeszukiwanie folderu {idx + 1}/{len(folders_to_search)}: {folder_name}")
                    
                    # Strategy varies by account type
                    messages_list = []
                    query_success = False
                    
                    if account_type == "exchange" and hasattr(search_folder, 'filter'):
                        # Exchange-specific folder operations
                        if combined_query:
                            try:
                                log(f"Próba zapytania z filtrami dla folderu '{folder_name}'")
                                messages = search_folder.filter(combined_query).order_by('-datetime_received')
                                messages_list = list(messages)
                                query_success = True
                                log(f"Zapytanie z filtrami: znaleziono {len(messages_list)} wiadomości")
                            except Exception as query_error:
                                log(f"BŁĄD zapytania z filtrami: {str(query_error)}")
                                # Query failed, fallback to getting all messages and filtering manually
                                try:
                                    log(f"Fallback: pobieranie wszystkich wiadomości z folderu '{folder_name}'")
                                    messages = search_folder.all().order_by('-datetime_received')
                                    messages_list = list(messages)
                                    log(f"Fallback: pobrano {len(messages_list)} wszystkich wiadomości")
                                except Exception as fallback_error:
                                    log(f"BŁĄD fallback: {str(fallback_error)}")
                        else:
                            try:
                                log(f"Pobieranie wszystkich wiadomości z folderu '{folder_name}' (brak filtrów)")
                                messages = search_folder.all().order_by('-datetime_received')
                                messages_list = list(messages)
                                log(f"Pobrano {len(messages_list)} wszystkich wiadomości")
                            except Exception as all_error:
                                log(f"BŁĄD pobierania wszystkich: {str(all_error)}")
                        
                        # If we still have no messages, try alternative QuerySet conversion
                        if not messages_list:
                            log(f"Brak wiadomości - próba alternatywnej metody konwersji")
                            try:
                                if combined_query:
                                    messages = search_folder.filter(combined_query)
                                else:
                                    messages = search_folder.all()
                                
                                # Use normal iteration instead of .iterator()
                                messages_list = [msg for msg in messages][:per_page]  # Limit during iteration
                                log(f"Alternatywna metoda: znaleziono {len(messages_list)} wiadomości (limit {per_page})")
                            except Exception as iteration_error:
                                log(f"BŁĄD alternatywnej metody: {str(iteration_error)}")
                                pass  # Continue with empty list
                    
                    else:
                        # IMAP/POP3 implementation using IMAPClient
                        log(f"Non-Exchange account type '{account_type}': Using IMAPClient message retrieval for folder '{folder_name}'")
                        messages_list = self._get_imap_messages(search_folder, connection, combined_query, criteria, account_type, per_page)
                        log(f"IMAP/POP3 retrieval completed: found {len(messages_list)} messages")
                    
                    # Apply per-folder limit
                    original_count = len(messages_list)
                    folder_messages = messages_list[:per_page]  # Limit per folder after converting to list
                    if original_count > per_page:
                        log(f"Ograniczono z {original_count} do {len(folder_messages)} wiadomości (limit na folder: {per_page})")
                    
                    log(f"Folder '{folder_name}' - szczegóły wiadomości:")
                    log(f"  - Znalezione wiadomości: {original_count}")
                    log(f"  - Po limicie folderu: {len(folder_messages)}")
                    log(f"  - Strategia pobierania: {'z filtrami' if query_success else 'wszystkie (fallback)'}")
                    
                    # Map each message to its folder path (DO NOT modify message objects)
                    # This avoids adding non-standard fields like _folder_reference to Message objects
                    folder_path_for_display = self._get_folder_path(search_folder)
                    for message in folder_messages:
                        # Use message ID or object reference as key to map to folder path
                        message_key = getattr(message, 'id', id(message))
                        message_to_folder_map[message_key] = folder_path_for_display
                    
                    all_messages.extend(folder_messages)
                    
                    # Store folder results for summary
                    folder_results[folder_name] = {
                        'original_count': original_count,
                        'limited_count': len(folder_messages),
                        'query_success': query_success
                    }
                    
                    log(f"Folder '{folder_name}': {len(folder_messages)} wiadomości dodano do wyników")
                    
                except Exception as e:
                    # Log the error but continue with other folders
                    error_msg = f"Błąd w folderze {folder_name}: {str(e)}"
                    log(f"BŁĄD FOLDERU '{folder_name}': {str(e)}")
                    folder_results[folder_name] = {'error': str(e)}
                    self.progress_callback(error_msg)
                    continue
            
            # Log folder search summary
            log("=== PODSUMOWANIE PRZESZUKIWANIA FOLDERÓW ===")
            total_messages_found = len(all_messages)
            log(f"Łącznie znaleziono {total_messages_found} wiadomości ze wszystkich folderów")
            
            for folder_name, result in folder_results.items():
                if 'error' in result:
                    log(f"  {folder_name}: BŁĄD - {result['error']}")
                else:
                    status = "z filtrami" if result['query_success'] else "wszystkie (fallback)"
                    if result['original_count'] != result['limited_count']:
                        log(f"  {folder_name}: {result['limited_count']} wiadomości ({status}, ograniczone z {result['original_count']})")
                    else:
                        log(f"  {folder_name}: {result['limited_count']} wiadomości ({status})")
            
            # Sort all messages by date
            all_messages.sort(key=lambda m: m.datetime_received if m.datetime_received else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            
            log("=== PRZETWARZANIE I FILTROWANIE WIADOMOŚCI ===")
            self.progress_callback("Przetwarzanie wiadomości...")
            
            # Calculate pagination
            start_idx = page * per_page
            end_idx = start_idx + per_page
            log(f"Paginacja: indeksy {start_idx}-{end_idx}")
            
            # Limit total messages for performance (use multiple of per_page to allow proper pagination)
            max_total_messages = max(per_page * 10, 1000)  # At least 10 pages worth, minimum 1000
            original_total = len(all_messages)
            total_messages = all_messages[:max_total_messages]
            total_count = len(total_messages)
            
            if original_total > max_total_messages:
                log(f"Ograniczono wiadomości z {original_total} do {total_count} (limit wydajności: {max_total_messages})")
            else:
                log(f"Przetwarzanie {total_count} wiadomości (bez ograniczeń)")
            
            # Filter by attachment criteria if needed  
            filtered_messages = []
            subject_search = criteria.get('subject_search', '').lower() if criteria.get('subject_search') else None
            pdf_search_text = criteria.get('pdf_search_text', '').strip() if criteria.get('pdf_search_text') else None
            has_attachment_filter = criteria.get('attachments_required') or criteria.get('no_attachments_only') or criteria.get('attachment_name') or criteria.get('attachment_extension')
            has_pdf_search = pdf_search_text is not None and len(pdf_search_text) > 0
            
            # Setup PDF auto-save if PDF search is enabled
            if has_pdf_search:
                self.auto_save_pdfs = True
                # Use configurable PDF save directory from criteria, fallback to default
                self.pdf_save_directory = criteria.get('pdf_save_directory') or os.path.join(os.getcwd(), "odczyty", "Faktury")
                self.saved_pdf_count = 0
                
                # Create output directory if it doesn't exist
                try:
                    os.makedirs(self.pdf_save_directory, exist_ok=True)
                    log(f"Przygotowano folder do automatycznego zapisu PDFów: {self.pdf_save_directory}")
                except Exception as e:
                    log(f"BŁĄD: Nie można utworzyć folderu {self.pdf_save_directory}: {e}")
                    self.progress_callback(f"BŁĄD: Nie można utworzyć folderu dla PDFów: {e}")
                    self.auto_save_pdfs = False
            else:
                self.auto_save_pdfs = False
                
            log("=== ETAPY FILTROWANIA ===")
            log(f"Wiadomości przed filtrowaniem: {len(total_messages)}")
            log(f"Kryteria filtrowania:")
            log(f"  - Filtr tematu: {'TAK (' + subject_search + ')' if subject_search else 'NIE'}")
            log(f"  - Wyszukiwanie w PDF: {'TAK (' + pdf_search_text + ')' if has_pdf_search else 'NIE'}")
            log(f"  - Automatyczny zapis PDFów: {'TAK' if self.auto_save_pdfs else 'NIE'}")
            log(f"  - Filtry załączników: {'TAK' if has_attachment_filter else 'NIE'}")
            if has_attachment_filter:
                if criteria.get('attachments_required'):
                    log(f"    - Wymagane załączniki: TAK")
                if criteria.get('no_attachments_only'):
                    log(f"    - Tylko bez załączników: TAK")
                if criteria.get('attachment_name'):
                    log(f"    - Nazwa załącznika zawiera: '{criteria['attachment_name']}'")
                if criteria.get('attachment_extension'):
                    log(f"    - Rozszerzenie załącznika: '{criteria['attachment_extension']}'")
                    
                # Check for conflicting attachment filters
                if criteria.get('attachments_required') and criteria.get('no_attachments_only'):
                    log(f"  ⚠️  OSTRZEŻENIE: Wybrano jednocześnie 'Tylko z załącznikami' i 'Tylko bez załączników'")
                    log(f"    Zostanie zastosowany filtr 'Tylko z załącznikami' (ma wyższy priorytet)")
            
            # Track filtering statistics
            subject_filtered_out = 0
            attachment_filtered_out = 0
            pdf_search_filtered_out = 0
            processing_errors = 0
            
            for message in total_messages:
                if self.search_cancelled:
                    log("Filtrowanie anulowane przez użytkownika")
                    self.result_callback({'type': 'search_cancelled'})
                    return
                
                try:
                    # Manual subject filtering (case-insensitive) - this acts as backup when query filtering didn't work properly
                    if subject_search:
                        message_subject = (message.subject or '').lower()
                        if subject_search not in message_subject:
                            subject_filtered_out += 1
                            continue
                    
                    # Manual sender filtering for fragments (case-insensitive)
                    if criteria.get('sender'):
                        sender_value = criteria['sender']
                        if not self._is_email_address(sender_value):
                            # This is a fragment, do local filtering
                            sender_fragment = sender_value.lower()
                            message_sender_matches = False
                            
                            # Check sender display name/email
                            if message.sender:
                                # For Exchange messages
                                if hasattr(message.sender, 'email_address') and message.sender.email_address:
                                    sender_email = message.sender.email_address.lower()
                                    if sender_fragment in sender_email:
                                        message_sender_matches = True
                                
                                # Check sender name if available
                                if hasattr(message.sender, 'name') and message.sender.name:
                                    sender_name = message.sender.name.lower()
                                    if sender_fragment in sender_name:
                                        message_sender_matches = True
                                
                                # For IMAP messages or fallback
                                sender_str = str(message.sender).lower()
                                if sender_fragment in sender_str:
                                    message_sender_matches = True
                            
                            if not message_sender_matches:
                                subject_filtered_out += 1  # Use same counter for simplicity
                                continue
                    
                    # Check attachment filters if needed
                    if has_attachment_filter:
                        if not self._check_attachment_filters(message, criteria):
                            attachment_filtered_out += 1
                            continue
                    
                    # Check PDF content search if needed
                    pdf_match_info = None
                    if has_pdf_search:
                        skip_searched_pdfs = criteria.get('skip_searched_pdfs', False)
                        pdf_match_result = self._check_pdf_content(message, pdf_search_text, skip_searched_pdfs)
                        if not pdf_match_result['found']:
                            pdf_search_filtered_out += 1
                            continue
                        else:
                            pdf_match_info = pdf_match_result  # Store for results display
                            
                    filtered_messages.append(message)
                    
                    # Store PDF match info if found (for later use in results)
                    if pdf_match_info:
                        # Use message ID or object reference as key to store PDF match info
                        message_key = getattr(message, 'id', id(message))
                        if not hasattr(self, '_pdf_matches'):
                            self._pdf_matches = {}
                        self._pdf_matches[message_key] = pdf_match_info
                    
                except Exception as filter_error:
                    # Skip messages that cause errors
                    processing_errors += 1
                    log(f"Błąd przetwarzania wiadomości: {str(filter_error)}")
                    continue
            
            # Log filtering results
            log(f"Wyniki filtrowania:")
            log(f"  - Wiadomości po filtrach: {len(filtered_messages)}")
            if subject_search:
                log(f"  - Odrzucone przez filtr tematu: {subject_filtered_out}")
            if has_attachment_filter:
                log(f"  - Odrzucone przez filtry załączników: {attachment_filtered_out}")
            if has_pdf_search:
                log(f"  - Odrzucone przez wyszukiwanie w PDF: {pdf_search_filtered_out}")
            if processing_errors > 0:
                log(f"  - Błędy przetwarzania: {processing_errors}")
            
            # FALLBACK: If filtering returned 0 results and we have a subject search, 
            # fetch all messages and filter manually by subject
            if len(filtered_messages) == 0 and subject_search and len(total_messages) > 0:
                log("=== FALLBACK: RĘCZNE FILTROWANIE PO TEMACIE ===")
                log(f"Filtracja zwróciła 0 wyników, próba ręcznego filtrowania {len(total_messages)} wiadomości po temacie: '{criteria['subject_search']}'")
                
                fallback_messages = []
                for message in total_messages:
                    try:
                        message_subject = (message.subject or '').lower()
                        if subject_search in message_subject:
                            fallback_messages.append(message)
                    except Exception as e:
                        log(f"Błąd ręcznego filtrowania wiadomości: {str(e)}")
                        continue
                
                log(f"Ręczne filtrowanie po temacie: znaleziono {len(fallback_messages)} wiadomości")
                if len(fallback_messages) > 0:
                    filtered_messages = fallback_messages
                    log("Używam wyników z ręcznego filtrowania fallback")
            
            # Apply pagination to filtered messages
            paginated_messages = filtered_messages[start_idx:end_idx]
            log(f"Wiadomości po paginacji: {len(paginated_messages)}")
            
            results = []
            result_processing_errors = 0
            
            log("=== TWORZENIE WYNIKÓW ===")
            for i, message in enumerate(paginated_messages):
                if self.search_cancelled:
                    log("Tworzenie wyników anulowane przez użytkownika")
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
                    
                    # Get folder path for this specific message from our mapping
                    message_key = getattr(message, 'id', id(message))
                    message_folder_path = message_to_folder_map.get(message_key, 'Skrzynka odbiorcza')
                    
                    # Get PDF match info if available
                    pdf_match_info = getattr(self, '_pdf_matches', {}).get(message_key, None)
                    
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
                        'attachments': list(message.attachments) if message.attachments else [],
                        'pdf_match_info': pdf_match_info  # Add PDF match information
                    }
                    results.append(result_info)
                    
                except Exception as e:
                    # Skip messages that cause errors
                    result_processing_errors += 1
                    log(f"Błąd przetwarzania wyniku {i}: {str(e)}")
                    continue
            
            if result_processing_errors > 0:
                log(f"Błędy przetwarzania wyników: {result_processing_errors}")
            
            # Log final summary
            log("=== PODSUMOWANIE WYSZUKIWANIA ===")
            log(f"Całkowita liczba folderów przeszukanych: {len(folders_to_search)}")
            log(f"Wiadomości znalezione ogółem: {total_messages_found}")
            log(f"Wiadomości po limitach i filtrach: {len(filtered_messages)}")
            log(f"Wiadomości na tej stronie: {len(results)}")
            log(f"Strona {page + 1} z {(len(filtered_messages) + per_page - 1) // per_page}")
            
            # Report PDF auto-save summary if enabled
            if self.auto_save_pdfs and has_pdf_search:
                if self.saved_pdf_count > 0:
                    summary_msg = f"Automatycznie zapisano {self.saved_pdf_count} plików PDF do: {self.pdf_save_directory}"
                    log(summary_msg)
                    self.progress_callback(summary_msg)
                else:
                    summary_msg = f"Nie znaleziono plików PDF zawierających '{pdf_search_text}'"
                    log(summary_msg)
                    self.progress_callback(summary_msg)
            
            log("=== KONIEC WYSZUKIWANIA ===")
            
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
            log(f"BŁĄD KRYTYCZNY wyszukiwania: {str(e)}")
            self.result_callback({
                'type': 'search_error',
                'error': str(e)
            })
    
    def _get_period_start_date(self, period):
        """Get start date for the selected period using proper datetime methods"""
        return IMAPDateHandler.get_period_start_date(period)

    def _get_safe_folder_name(self, folder):
        """Safely extract folder name from folder object or string"""
        try:
            if not folder:
                return 'Skrzynka odbiorcza'
            
            # If it's a string (IMAP/POP3), return it directly
            if isinstance(folder, str):
                if folder.upper() == 'INBOX':
                    return 'Skrzynka odbiorcza'
                return folder
            
            # If it's an object with .name attribute (Exchange), use that
            if hasattr(folder, 'name'):
                return folder.name
            
            # Fallback to string representation
            return str(folder)
            
        except Exception as e:
            log(f"Error extracting folder name: {str(e)}")
            return 'Skrzynka odbiorcza'

    def _get_folder_path(self, folder):
        """Get the full folder path from folder object"""
        try:
            if not folder:
                return 'Skrzynka odbiorcza'
            
            # Handle string folders (IMAP/POP3)
            if isinstance(folder, str):
                if folder.upper() == 'INBOX':
                    return 'Skrzynka odbiorcza'
                return folder
            
            # Handle Exchange folder objects - build path by traversing up the folder hierarchy
            if hasattr(folder, 'name'):
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
            
            # Fallback for unknown object types
            return str(folder)
                
        except Exception as e:
            # Fallback to folder name or generic name
            try:
                if isinstance(folder, str):
                    return folder
                return folder.name if hasattr(folder, 'name') else 'Skrzynka odbiorcza'
            except:
                return 'Skrzynka odbiorcza'

    def _get_monthly_folder_path(self, base_directory, email_date):
        """Create monthly folder path based on email date using proper datetime methods"""
        try:
            # Use IMAPDateHandler for proper date formatting - no split() operations
            month_year = IMAPDateHandler.format_monthly_folder(email_date)
            monthly_folder = os.path.join(base_directory, month_year)
            return monthly_folder
        except Exception as e:
            log(f"BŁĄD przy tworzeniu ścieżki miesięcznego folderu: {e}")
            return base_directory  # Fallback to base directory
    
    def _check_attachment_filters(self, message, criteria):
        """Check if message meets attachment criteria"""
        if criteria.get('attachments_required') and not message.has_attachments:
            return False
        
        # Check for "only without attachments" filter only if "attachments_required" is not set
        # This gives priority to "attachments_required" when both filters are conflicting
        if not criteria.get('attachments_required') and criteria.get('no_attachments_only') and message.has_attachments:
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
    
    def _check_pdf_content(self, message, search_text, skip_searched_pdfs=False):
        """Check if message has PDF attachments containing the search text"""
        if not message.attachments or not search_text:
            return {'found': False, 'matches': [], 'method': 'no_attachments_or_text'}
        
        found_matches = []
        found_attachment_names = []
        skipped_pdfs_count = 0
        
        for attachment in message.attachments:
            if self.search_cancelled:
                return {'found': False, 'matches': [], 'method': 'cancelled'}
            
            # Check if attachment is a PDF
            attachment_name = getattr(attachment, 'name', '') or ''
            if not attachment_name.lower().endswith('.pdf'):
                continue
            
            # Check if we should skip this PDF based on history
            if skip_searched_pdfs and self.pdf_history_manager:
                try:
                    attachment_content = getattr(attachment, 'content', None)
                    if attachment_content and self.pdf_history_manager.is_pdf_already_searched(
                        attachment_name, attachment_content, search_text
                    ):
                        # Mark as skipped and continue to next attachment
                        self.pdf_history_manager.mark_pdf_as_skipped(
                            attachment_name, attachment_content, search_text
                        )
                        skipped_pdfs_count += 1
                        log(f"[PDF HISTORY] Pominięto już przeszukany PDF: {attachment_name}")
                        continue
                except Exception as e:
                    log(f"[PDF HISTORY] Błąd sprawdzania historii dla {attachment_name}: {e}")
                    # Continue with search if history check fails
            
            # Search in this PDF attachment
            result = self.pdf_processor.search_in_pdf_attachment(attachment, search_text, attachment_name)
            
            if result['found']:
                found_matches.extend(result.get('matches', []))
                found_attachment_names.append({
                    'name': attachment_name,
                    'method': result.get('method', 'unknown'),
                    'matches': result.get('matches', [])
                })
                
                # Mark PDF as searched in history
                if self.pdf_history_manager:
                    try:
                        attachment_content = getattr(attachment, 'content', None)
                        if attachment_content:
                            # Get sender email from message
                            sender_email = getattr(message.sender, 'email_address', None) if hasattr(message, 'sender') else None
                            self.pdf_history_manager.mark_pdf_as_searched(
                                attachment_name, attachment_content, search_text, result.get('matches', []), sender_email
                            )
                    except Exception as e:
                        log(f"[PDF HISTORY] Błąd oznaczania PDF {attachment_name} jako przeszukany: {e}")
                
                # Auto-save PDF if enabled
                if self.auto_save_pdfs and self.pdf_save_directory:
                    try:
                        # Get monthly folder path based on email date
                        monthly_folder = self._get_monthly_folder_path(self.pdf_save_directory, message.datetime_received)
                        
                        # Create monthly folder if it doesn't exist
                        try:
                            os.makedirs(monthly_folder, exist_ok=True)
                        except Exception as e:
                            log(f"BŁĄD: Nie można utworzyć miesięcznego folderu {monthly_folder}: {e}")
                            monthly_folder = self.pdf_save_directory  # Fallback to main directory
                        
                        # Create safe filename (remove/replace problematic characters)
                        safe_filename = "".join(c for c in attachment_name if c.isalnum() or c in (' ', '.', '_', '-', '(', ')'))
                        if not safe_filename:
                            safe_filename = f"attachment_{self.saved_pdf_count + 1}.pdf"
                        
                        output_path = os.path.join(monthly_folder, safe_filename)
                        
                        # Write PDF content to file (overwrite if exists to avoid duplicates)
                        with open(output_path, 'wb') as f:
                            f.write(attachment.content)
                        
                        # Set file modification time to match email date using proper methods
                        if message.datetime_received:
                            try:
                                # Use IMAPDateHandler for timestamp conversion - no split()
                                email_timestamp = IMAPDateHandler.convert_to_timestamp(message.datetime_received)
                                if email_timestamp:
                                    # Set both access time and modification time to email date
                                    os.utime(output_path, (email_timestamp, email_timestamp))
                                    log(f"Ustawiono datę modyfikacji pliku {safe_filename} na: {message.datetime_received}")
                            except Exception as e:
                                log(f"OSTRZEŻENIE: Nie można ustawić daty modyfikacji pliku {safe_filename}: {e}")
                        
                        self.saved_pdf_count += 1
                        
                        # Log successful save with folder information
                        subject = (message.subject[:50] + "...") if message.subject and len(message.subject) > 50 else (message.subject or "Bez tematu")
                        folder_name = os.path.basename(monthly_folder)
                        log(f"Auto-zapisano PDF: {safe_filename} do folderu {folder_name}/ (z wiadomości: {subject})")
                        self.progress_callback(f"Zapisano: {safe_filename} -> {folder_name}/")
                        
                    except Exception as e:
                        log(f"BŁĄD auto-zapisu PDF {attachment_name}: {e}")
                        # Don't stop processing, just log the error
            else:
                # Mark PDF as searched in history even if no matches found
                if self.pdf_history_manager:
                    try:
                        attachment_content = getattr(attachment, 'content', None)
                        if attachment_content:
                            # Get sender email from message
                            sender_email = getattr(message.sender, 'email_address', None) if hasattr(message, 'sender') else None
                            self.pdf_history_manager.mark_pdf_as_searched(
                                attachment_name, attachment_content, search_text, [], sender_email
                            )
                    except Exception as e:
                        log(f"[PDF HISTORY] Błąd oznaczania PDF {attachment_name} jako przeszukany (bez wyników): {e}")
        
        # Log statistics about skipped PDFs
        if skipped_pdfs_count > 0:
            log(f"[PDF HISTORY] Pominięto {skipped_pdfs_count} już przeszukanych PDF-ów")
        
        if found_attachment_names:
            return {
                'found': True,
                'attachments': found_attachment_names,
                'all_matches': found_matches,
                'skipped_count': skipped_pdfs_count
            }
        
        return {'found': False, 'matches': [], 'method': 'not_found_in_pdfs', 'skipped_count': skipped_pdfs_count}

    def _get_imap_messages(self, folder_name, connection, combined_query, criteria, account_type, per_page=500):
        """Retrieve messages from IMAP folder using IMAPClient"""
        try:
            if account_type == "pop3_smtp":
                return self._get_pop3_messages(connection, criteria, per_page)
            
            # For IMAP accounts, use the existing IMAP connection
            imap = connection.imap_connection
            if not imap:
                log("[IMAP] ERROR: No IMAP connection available")
                return []
            
            # Select the folder
            try:
                if isinstance(folder_name, str):
                    imap.select_folder(folder_name)
                    log(f"[IMAP] Selected folder: {folder_name}")
                else:
                    # Should not happen for IMAP, but fallback to INBOX
                    imap.select_folder("INBOX")
                    log(f"[IMAP] Fallback to INBOX folder")
            except Exception as folder_error:
                log(f"[IMAP] ERROR selecting folder {folder_name}: {str(folder_error)}")
                try:
                    imap.select_folder("INBOX")
                    log("[IMAP] Fallback to INBOX after folder selection error")
                except Exception as inbox_error:
                    log(f"[IMAP] ERROR: Cannot even select INBOX: {str(inbox_error)}")
                    return []
            
            # Build IMAP search criteria
            search_criteria = self._build_imap_search_criteria(criteria)
            log(f"[IMAP] Search criteria: {search_criteria}")
            
            # Search for message UIDs
            try:
                message_uids = imap.search(search_criteria)
                log(f"[IMAP] Found {len(message_uids)} messages matching criteria")
            except Exception as search_error:
                log(f"[IMAP] Search failed: {str(search_error)}, falling back to ALL")
                try:
                    message_uids = imap.search(['ALL'])
                    log(f"[IMAP] Fallback search found {len(message_uids)} messages")
                except Exception as fallback_error:
                    log(f"[IMAP] ERROR: Even fallback search failed: {str(fallback_error)}")
                    return []
            
            if not message_uids:
                log("[IMAP] No messages found")
                return []
            
            # Limit the number of messages for performance
            limited_uids = message_uids[-per_page:]  # Get most recent messages up to per_page limit
            if len(limited_uids) < len(message_uids):
                log(f"[IMAP] Limited to {len(limited_uids)} most recent messages (from {len(message_uids)} total)")
            
            # Fetch message data
            log(f"[IMAP] Fetching message data for {len(limited_uids)} messages...")
            messages_list = self._fetch_imap_messages(imap, limited_uids, criteria)
            
            log(f"[IMAP] Successfully retrieved {len(messages_list)} message objects")
            return messages_list
            
        except Exception as e:
            log(f"[IMAP] ERROR in _get_imap_messages: {str(e)}")
            return []
    
    def _build_imap_search_criteria(self, criteria):
        """Build IMAP search criteria from GUI criteria as flat list"""
        search_terms = []
        
        # Subject search
        if criteria.get('subject_search'):
            search_terms.extend(['SUBJECT', criteria['subject_search']])
            log(f"[IMAP] Adding subject search: {criteria['subject_search']}")
        
        # Body search
        if criteria.get('body_search'):
            search_terms.extend(['BODY', criteria['body_search']])
            log(f"[IMAP] Adding body search: {criteria['body_search']}")
        
        # Sender search - use IMAP FROM filter only for full email addresses
        if criteria.get('sender'):
            sender_value = criteria['sender']
            if self._is_email_address(sender_value):
                # Full email address - use IMAP FROM filter
                search_terms.extend(['FROM', sender_value])
                log(f"[IMAP] Adding sender search (full email): {sender_value}")
            else:
                # Fragment - skip IMAP filter, will filter locally later
                log(f"[IMAP] Sender fragment detected: '{sender_value}' - skipping IMAP FROM filter, will use local filtering")
        
        # Unread only
        if criteria.get('unread_only'):
            search_terms.append('UNSEEN')
            log("[IMAP] Adding unread only filter")
        
        # Date period filter
        if criteria.get('selected_period') and criteria['selected_period'] != 'wszystkie':
            start_date = self._get_period_start_date(criteria['selected_period'])
            if start_date:
                # Format date for IMAP using proper datetime methods - no split()
                date_str = IMAPDateHandler.format_imap_search_date(start_date)
                if date_str:
                    search_terms.extend(['SINCE', date_str])
                    log(f"[IMAP] Adding date filter: since {date_str}")
        
        # If no criteria specified, return ALL
        if not search_terms:
            search_terms = ['ALL']
        
        return search_terms
    
    def _fetch_imap_messages(self, imap, message_uids, criteria):
        """Fetch and parse IMAP messages"""
        messages_list = []
        
        try:
            # Fetch message data in batches
            batch_size = 50
            for i in range(0, len(message_uids), batch_size):
                if self.search_cancelled:
                    log("[IMAP] Message fetching cancelled")
                    break
                
                batch_uids = message_uids[i:i + batch_size]
                log(f"[IMAP] Fetching batch {i//batch_size + 1}: UIDs {len(batch_uids)} messages")
                
                try:
                    # Fetch headers and basic info
                    response = imap.fetch(batch_uids, ['ENVELOPE', 'FLAGS', 'RFC822.SIZE', 'BODYSTRUCTURE'])
                    
                    for uid in batch_uids:
                        if self.search_cancelled:
                            break
                        
                        if uid in response:
                            try:
                                message_obj = self._parse_imap_message(imap, uid, response[uid], criteria)
                                if message_obj:
                                    messages_list.append(message_obj)
                            except Exception as parse_error:
                                log(f"[IMAP] Error parsing message UID {uid}: {str(parse_error)}")
                                continue
                
                except Exception as batch_error:
                    log(f"[IMAP] Error fetching batch: {str(batch_error)}")
                    continue
        
        except Exception as e:
            log(f"[IMAP] ERROR in _fetch_imap_messages: {str(e)}")
        
        return messages_list
    
    def _parse_imap_message(self, imap, uid, message_data, criteria):
        """Parse IMAP message data into a message-like object"""
        try:
            envelope = message_data.get(b'ENVELOPE')
            flags = message_data.get(b'FLAGS', [])
            bodystructure = message_data.get(b'BODYSTRUCTURE')
            size = message_data.get(b'RFC822.SIZE', 0)
            
            if not envelope:
                log(f"[IMAP] No envelope data for UID {uid}")
                return None
            
            # Parse envelope data
            subject = self._decode_imap_header(envelope.subject) if envelope.subject else "Brak tematu"
            sender_info = envelope.sender[0] if envelope.sender and len(envelope.sender) > 0 else None
            from_info = envelope.from_[0] if envelope.from_ and len(envelope.from_) > 0 else None
            
            # Get sender email and name
            sender_email = None
            sender_name = None
            if sender_info:
                sender_email = self._decode_imap_header(sender_info.mailbox) + "@" + self._decode_imap_header(sender_info.host)
                sender_name = self._decode_imap_header(sender_info.name) if sender_info.name else None
            elif from_info:
                sender_email = self._decode_imap_header(from_info.mailbox) + "@" + self._decode_imap_header(from_info.host)
                sender_name = self._decode_imap_header(from_info.name) if from_info.name else None
            
            sender_display = sender_name if sender_name else (sender_email if sender_email else "Nieznany")
            
            # Parse date using robust datetime handler - no split() operations
            if envelope.date:
                date_received = IMAPDateHandler.parse_imap_date(envelope.date)
            else:
                date_received = datetime.now(timezone.utc)
            
            # Determine if message is read
            is_read = b'\\Seen' in flags
            
            # Check for attachments
            has_attachments = self._check_imap_attachments(bodystructure)
            
            # Create a message-like object
            message_obj = IMAPMessage(
                uid=uid,
                subject=subject,
                sender=IMAPSender(sender_display, sender_email),
                datetime_received=date_received,
                is_read=is_read,
                has_attachments=has_attachments,
                imap_connection=imap,
                size=size,
                bodystructure=bodystructure
            )
            
            return message_obj
            
        except Exception as e:
            log(f"[IMAP] ERROR parsing message UID {uid}: {str(e)}")
            return None
    
    def _decode_imap_header(self, header_value):
        """Decode IMAP header value"""
        if not header_value:
            return ""
        
        try:
            if isinstance(header_value, bytes):
                header_value = header_value.decode('utf-8', errors='ignore')
            
            # Decode RFC2047 encoded headers
            decoded_parts = email.header.decode_header(str(header_value))
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            part = part.decode(encoding)
                        except:
                            part = part.decode('utf-8', errors='ignore')
                    else:
                        part = part.decode('utf-8', errors='ignore')
                decoded_string += part
            
            return decoded_string.strip()
            
        except Exception as e:
            log(f"[IMAP] Error decoding header: {str(e)}")
            return str(header_value) if header_value else ""
    
    def _check_imap_attachments(self, bodystructure):
        """Check if IMAP message has attachments based on bodystructure"""
        if not bodystructure:
            return False
        
        try:
            # Recursively check bodystructure for attachments
            return self._has_attachments_recursive(bodystructure)
        except Exception as e:
            log(f"[IMAP] Error checking attachments: {str(e)}")
            return False
    
    def _has_attachments_recursive(self, structure):
        """Recursively check bodystructure for attachments"""
        if not structure:
            return False
        
        try:
            # If it's a tuple/list and has multiple parts
            if isinstance(structure, (tuple, list)) and len(structure) > 0:
                # Check if this is a multipart structure
                if isinstance(structure[0], (tuple, list)):
                    # Multipart - check each part
                    for part in structure:
                        if isinstance(part, (tuple, list)) and self._has_attachments_recursive(part):
                            return True
                else:
                    # Single part - check disposition
                    if len(structure) > 8:
                        disposition = structure[8] if len(structure) > 8 else None
                        if disposition and isinstance(disposition, (tuple, list)) and len(disposition) > 0:
                            if disposition[0] and b'attachment' in disposition[0].lower():
                                return True
            
            return False
            
        except Exception as e:
            log(f"[IMAP] Error in recursive attachment check: {str(e)}")
            return False
    
    def _get_pop3_messages(self, connection, criteria, per_page=500):
        """Retrieve messages from POP3 connection"""
        try:
            pop3 = connection.pop3_connection
            if not pop3:
                log("[POP3] ERROR: No POP3 connection available")
                return []
            
            log("[POP3] Retrieving message list...")
            messages_list = []
            
            # Get message count
            num_messages = len(pop3.list()[1])
            log(f"[POP3] Found {num_messages} messages")
            
            # Limit messages for performance
            max_messages = min(num_messages, per_page)
            start_index = max(1, num_messages - max_messages + 1)
            
            log(f"[POP3] Retrieving {max_messages} most recent messages (from {start_index} to {num_messages})")
            
            for i in range(start_index, num_messages + 1):
                if self.search_cancelled:
                    log("[POP3] Message retrieval cancelled")
                    break
                
                try:
                    # Get message headers
                    response = pop3.top(i, 0)  # Get headers only
                    if response:
                        header_lines = response[1]
                        header_text = b'\n'.join(header_lines).decode('utf-8', errors='ignore')
                        
                        # Parse headers
                        msg = email.message_from_string(header_text)
                        
                        # Create message object
                        message_obj = self._create_pop3_message_object(i, msg, pop3)
                        if message_obj:
                            messages_list.append(message_obj)
                
                except Exception as msg_error:
                    log(f"[POP3] Error retrieving message {i}: {str(msg_error)}")
                    continue
            
            log(f"[POP3] Successfully retrieved {len(messages_list)} messages")
            return messages_list
            
        except Exception as e:
            log(f"[POP3] ERROR in _get_pop3_messages: {str(e)}")
            return []
    
    def _create_pop3_message_object(self, message_num, email_msg, pop3_connection):
        """Create a message-like object from POP3 email"""
        try:
            # Extract basic info
            subject = self._decode_imap_header(email_msg.get('Subject', 'Brak tematu'))
            from_header = email_msg.get('From', 'Nieznany')
            sender_display = self._decode_imap_header(from_header)
            date_header = email_msg.get('Date')
            
            # Parse date using robust datetime handler - no split() operations
            date_received = IMAPDateHandler.parse_imap_date(date_header)
            
            # POP3 messages are always considered read
            is_read = True
            
            # Check for attachments by examining Content-Type
            has_attachments = email_msg.is_multipart()
            
            # Create message object
            message_obj = POP3Message(
                message_num=message_num,
                subject=subject,
                sender=IMAPSender(sender_display, from_header),
                datetime_received=date_received,
                is_read=is_read,
                has_attachments=has_attachments,
                pop3_connection=pop3_connection,
                email_message=email_msg
            )
            
            return message_obj
            
        except Exception as e:
            log(f"[POP3] Error creating message object: {str(e)}")
            return None


class IMAPSender:
    """Simple sender object compatible with Exchange sender interface"""
    def __init__(self, display_name, email_address):
        self.name = display_name
        self.email_address = email_address
    
    def __str__(self):
        return self.name if self.name else self.email_address


class IMAPMessage:
    """Message object for IMAP messages, compatible with Exchange Message interface"""
    def __init__(self, uid, subject, sender, datetime_received, is_read, has_attachments, 
                 imap_connection, size=0, bodystructure=None):
        self.id = uid
        self.uid = uid
        self.subject = subject
        self.sender = sender
        self.datetime_received = datetime_received
        self.datetime_sent = datetime_received  # Use received time as sent time approximation
        self.datetime_created = datetime_received
        self.is_read = is_read
        self.has_attachments = has_attachments
        self.size = size
        self.bodystructure = bodystructure
        self._imap_connection = imap_connection
        self._attachments = None
        self._body = None
    
    @property
    def attachments(self):
        """Lazy load attachments when requested"""
        if self._attachments is None:
            self._attachments = self._load_attachments()
        return self._attachments
    
    @property
    def body(self):
        """Lazy load message body when requested"""
        if self._body is None:
            self._body = self._load_body()
        return self._body
    
    def _load_attachments(self):
        """Load attachments from IMAP message"""
        try:
            if not self.has_attachments:
                return []
            
            log(f"[IMAP] Loading attachments for message UID {self.uid}")
            
            # Fetch the full message to get attachments
            response = self._imap_connection.fetch([self.uid], ['RFC822'])
            if self.uid not in response:
                log(f"[IMAP] Could not fetch full message for UID {self.uid}")
                return []
            
            raw_message = response[self.uid][b'RFC822']
            email_msg = email.message_from_bytes(raw_message)
            
            attachments = []
            for part in email_msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        content = part.get_payload(decode=True)
                        if content:
                            attachment = IMAPAttachment(filename, content)
                            attachments.append(attachment)
                            log(f"[IMAP] Found attachment: {filename}")
            
            log(f"[IMAP] Loaded {len(attachments)} attachments for UID {self.uid}")
            return attachments
            
        except Exception as e:
            log(f"[IMAP] Error loading attachments for UID {self.uid}: {str(e)}")
            return []
    
    def _load_body(self):
        """Load message body from IMAP message"""
        try:
            log(f"[IMAP] Loading body for message UID {self.uid}")
            
            # Try to get just the text parts first
            response = self._imap_connection.fetch([self.uid], ['BODY[TEXT]'])
            if self.uid in response and b'BODY[TEXT]' in response[self.uid]:
                body_text = response[self.uid][b'BODY[TEXT]']
                if isinstance(body_text, bytes):
                    return body_text.decode('utf-8', errors='ignore')
                return str(body_text)
            
            # Fallback to full message
            response = self._imap_connection.fetch([self.uid], ['RFC822'])
            if self.uid not in response:
                return ""
            
            raw_message = response[self.uid][b'RFC822']
            email_msg = email.message_from_bytes(raw_message)
            
            # Extract text content
            body_text = ""
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            body_text += payload.decode(charset, errors='ignore')
                        except:
                            body_text += payload.decode('utf-8', errors='ignore')
                        body_text += "\n"
            
            return body_text.strip()
            
        except Exception as e:
            log(f"[IMAP] Error loading body for UID {self.uid}: {str(e)}")
            return ""


class IMAPAttachment:
    """Attachment object for IMAP messages"""
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content) if content else 0
    
    def __str__(self):
        return f"IMAPAttachment(name={self.name}, size={self.size})"


class POP3Message:
    """Message object for POP3 messages, compatible with Exchange Message interface"""
    def __init__(self, message_num, subject, sender, datetime_received, is_read, has_attachments,
                 pop3_connection, email_message):
        self.id = message_num
        self.message_num = message_num
        self.subject = subject
        self.sender = sender
        self.datetime_received = datetime_received
        self.datetime_sent = datetime_received
        self.datetime_created = datetime_received
        self.is_read = is_read
        self.has_attachments = has_attachments
        self._pop3_connection = pop3_connection
        self._email_message = email_message
        self._attachments = None
        self._body = None
    
    @property
    def attachments(self):
        """Lazy load attachments when requested"""
        if self._attachments is None:
            self._attachments = self._load_attachments()
        return self._attachments
    
    @property
    def body(self):
        """Lazy load message body when requested"""
        if self._body is None:
            self._body = self._load_body()
        return self._body
    
    def _load_attachments(self):
        """Load attachments from POP3 message"""
        try:
            if not self.has_attachments:
                return []
            
            log(f"[POP3] Loading attachments for message {self.message_num}")
            
            # Get full message
            response = self._pop3_connection.retr(self.message_num)
            if not response:
                return []
            
            full_message = b'\n'.join(response[1])
            email_msg = email.message_from_bytes(full_message)
            
            attachments = []
            for part in email_msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        content = part.get_payload(decode=True)
                        if content:
                            attachment = IMAPAttachment(filename, content)
                            attachments.append(attachment)
                            log(f"[POP3] Found attachment: {filename}")
            
            log(f"[POP3] Loaded {len(attachments)} attachments for message {self.message_num}")
            return attachments
            
        except Exception as e:
            log(f"[POP3] Error loading attachments for message {self.message_num}: {str(e)}")
            return []
    
    def _load_body(self):
        """Load message body from POP3 message"""
        try:
            log(f"[POP3] Loading body for message {self.message_num}")
            
            # Get full message
            response = self._pop3_connection.retr(self.message_num)
            if not response:
                return ""
            
            full_message = b'\n'.join(response[1])
            email_msg = email.message_from_bytes(full_message)
            
            # Extract text content
            body_text = ""
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            body_text += payload.decode(charset, errors='ignore')
                        except:
                            body_text += payload.decode('utf-8', errors='ignore')
                        body_text += "\n"
            
            return body_text.strip()
            
        except Exception as e:
            log(f"[POP3] Error loading body for message {self.message_num}: {str(e)}")
            return ""