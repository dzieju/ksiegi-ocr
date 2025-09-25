"""
Email search engine for mail search functionality
"""
import threading
import queue
import os
import time
from datetime import datetime, timedelta, timezone
# TODO: exchangelib import could be lazy-loaded for better startup performance
from exchangelib import Q, Message  # Heavy import - consider lazy loading if startup optimization needed
from tools.logger import log
from .pdf_processor import PDFProcessor

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
        
        # Cache valid Message field names for validation
        self._valid_fields = self._get_valid_message_fields()
        log(f"Zainicjalizowano wyszukiwarkę z {len(self._valid_fields)} dostępnymi polami Message")
    
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
            
            # Get account for folder operations
            account = connection.get_account()
            if not account:
                log("BŁĄD: Nie można nawiązać połączenia z serwerem poczty")
                raise Exception("Nie można nawiązać połączenia z serwerem poczty")
            
            log(f"Połączono z kontem: {account.primary_smtp_address}")
            
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
                log(f"  {i}. {folder.name}")
            
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
            
            # Sender filter
            if criteria.get('sender'):
                sender_filter = self._create_safe_filter('sender', criteria['sender'], 'icontains')
                if sender_filter:
                    query_filters.append(sender_filter)
                    log(f"Dodano filtr nadawcy (case-insensitive): '{criteria['sender']}'")
                else:
                    log(f"POMINIĘTO nieprawidłowy filtr nadawcy")
            
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
                
                folder_name = search_folder.name
                log(f"--- Folder {idx + 1}/{len(folders_to_search)}: '{folder_name}' ---")
                
                try:
                    self.progress_callback(f"Przeszukiwanie folderu {idx + 1}/{len(folders_to_search)}: {folder_name}")
                    
                    # Strategy: First try with query if we have one, if that fails or returns empty, try without query
                    messages_list = []
                    query_success = False
                    
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
                                log(f"Fallback: pobrано {len(messages_list)} wszystkich wiadomości")
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
                            messages_list = [msg for msg in messages][:100]  # Limit during iteration
                            log(f"Alternatywna metoda: znaleziono {len(messages_list)} wiadomości (limit 100)")
                        except Exception as iteration_error:
                            log(f"BŁĄD alternatywnej metody: {str(iteration_error)}")
                            pass  # Continue with empty list
                    
                    # Apply per-folder limit
                    original_count = len(messages_list)
                    folder_messages = messages_list[:100]  # Limit per folder after converting to list
                    if original_count > 100:
                        log(f"Ograniczono z {original_count} do {len(folder_messages)} wiadomości (limit na folder)")
                    
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
            
            # Limit total messages for performance (500 total across all folders)
            original_total = len(all_messages)
            total_messages = all_messages[:500]
            total_count = len(total_messages)
            
            if original_total > 500:
                log(f"Ograniczono wiadomości z {original_total} do {total_count} (limit wydajności)")
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
                self.pdf_save_directory = os.path.join(os.getcwd(), "odczyty", "Faktury")
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
                    
                    # Check attachment filters if needed
                    if has_attachment_filter:
                        if not self._check_attachment_filters(message, criteria):
                            attachment_filtered_out += 1
                            continue
                    
                    # Check PDF content search if needed
                    pdf_match_info = None
                    if has_pdf_search:
                        pdf_match_result = self._check_pdf_content(message, pdf_search_text)
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

    def _get_monthly_folder_path(self, base_directory, email_date):
        """Create monthly folder path based on email date (MM.YYYY format)"""
        try:
            if not email_date:
                # If no date, use current date as fallback
                from datetime import datetime
                email_date = datetime.now()
            
            # Format: MM.YYYY (e.g., 09.2025)
            month_year = email_date.strftime("%m.%Y")
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
    
    def _check_pdf_content(self, message, search_text):
        """Check if message has PDF attachments containing the search text"""
        if not message.attachments or not search_text:
            return {'found': False, 'matches': [], 'method': 'no_attachments_or_text'}
        
        found_matches = []
        found_attachment_names = []
        
        for attachment in message.attachments:
            if self.search_cancelled:
                return {'found': False, 'matches': [], 'method': 'cancelled'}
            
            # Check if attachment is a PDF
            attachment_name = getattr(attachment, 'name', '') or ''
            if not attachment_name.lower().endswith('.pdf'):
                continue
            
            # Search in this PDF attachment
            result = self.pdf_processor.search_in_pdf_attachment(attachment, search_text, attachment_name)
            
            if result['found']:
                found_matches.extend(result.get('matches', []))
                found_attachment_names.append({
                    'name': attachment_name,
                    'method': result.get('method', 'unknown'),
                    'matches': result.get('matches', [])
                })
                
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
                        
                        # Set file modification time to match email date
                        if message.datetime_received:
                            try:
                                # Convert datetime to timestamp for os.utime
                                email_timestamp = message.datetime_received.timestamp()
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
        
        if found_attachment_names:
            return {
                'found': True,
                'attachments': found_attachment_names,
                'all_matches': found_matches
            }
        
        return {'found': False, 'matches': [], 'method': 'not_found_in_pdfs'}