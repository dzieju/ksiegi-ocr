"""
Search functionality including threading, queues, and filtering logic.
"""
import threading
import queue
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from exchangelib import errors, Q


class SearchManager:
    """Manages threaded search operations with progress tracking."""
    
    def __init__(self):
        self.search_cancelled = False
        self.search_executor = None
        self.result_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.search_thread = None
    
    def start_search(self, search_function, *args, **kwargs):
        """Start a search operation in a background thread."""
        self.search_cancelled = False
        self.search_thread = threading.Thread(
            target=search_function,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self.search_thread.start()
        return self.search_thread
    
    def cancel_search(self):
        """Cancel ongoing search operation."""
        self.search_cancelled = True
        if self.search_executor:
            self.search_executor.shutdown(wait=False)
    
    def is_search_active(self):
        """Check if search is currently running."""
        return self.search_thread and self.search_thread.is_alive()
    
    def get_results(self):
        """Get all available results from the result queue."""
        results = []
        try:
            while True:
                try:
                    result = self.result_queue.get_nowait()
                    results.append(result)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki wyników: {e}")
        return results
    
    def get_progress_updates(self):
        """Get all available progress updates from the progress queue."""
        updates = []
        try:
            while True:
                try:
                    progress = self.progress_queue.get_nowait()
                    updates.append(progress)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Błąd przetwarzania kolejki postępu: {e}")
        return updates


class EmailSearcher:
    """Handles email search operations with PDF attachment processing."""
    
    def __init__(self, exchange_connection, pdf_processor):
        self.exchange_connection = exchange_connection
        self.pdf_processor = pdf_processor
        self.search_manager = SearchManager()
    
    def search_emails_for_nip(self, nip, folder_name, date_from, date_to, 
                             search_all_folders=False, excluded_folders=None, 
                             exclude_mode=False, folder_list=None):
        """
        Search emails for NIP in PDF attachments.
        This is the main search logic that runs in a background thread.
        """
        try:
            seen_filenames = set()
            attachment_counter = 0
            excluded_folders = excluded_folders or set()
            folder_list = folder_list or []

            print(f"Zakres dat do szukania: date_from={date_from}, date_to={date_to}")

            # Determine folders to search
            folders_to_search = self._determine_search_folders(
                search_all_folders, exclude_mode, excluded_folders, 
                folder_list, folder_name
            )
            
            if not folders_to_search:
                self.search_manager.progress_queue.put("Brak folderów do przeszukania")
                self.search_manager.result_queue.put({'type': 'search_complete'})
                return

            # Collect all PDF attachments first
            all_attachments = self._collect_pdf_attachments(
                folders_to_search, date_from, date_to, seen_filenames, attachment_counter
            )

            if self.search_manager.search_cancelled:
                self.search_manager.result_queue.put({'type': 'search_complete'})
                return

            # Process PDF attachments with threading
            self._process_attachments_threaded(all_attachments, nip, seen_filenames)

            # Complete the search
            self.search_manager.result_queue.put({'type': 'search_complete'})

        except Exception as e:
            tb = traceback.format_exc()
            print(f"Błąd połączenia: {e}\n{tb}")
            self.search_manager.progress_queue.put(f"Błąd: {str(e)}")
            self.search_manager.result_queue.put({'type': 'search_complete'})
    
    def _determine_search_folders(self, search_all_folders, exclude_mode, 
                                excluded_folders, folder_list, folder_name):
        """Determine which folders should be searched based on settings."""
        finder = lambda name: self.exchange_connection.find_folder_by_display_name(name)

        if search_all_folders:
            if exclude_mode:
                print("Tryb: szukaj TYLKO w wybranych folderach.")
                folders_to_search = [
                    finder(f) for f in excluded_folders
                ]
            else:
                print("Tryb: pomiń wykluczone foldery.")
                folders_to_search = [
                    finder(f) for f in folder_list if f not in excluded_folders
                ]
        else:
            folder = finder(folder_name)
            if folder is None:
                print(f"Błąd: nie znaleziono folderu: {folder_name}")
                self.search_manager.progress_queue.put(f"Błąd: nie znaleziono folderu: {folder_name}")
                return []
            
            # Validate folder exclusion settings
            if not exclude_mode and folder_name in excluded_folders:
                print(f"Błąd: wybrany folder {folder_name} jest na liście wykluczonych.")
                self.search_manager.progress_queue.put(f"Błąd: folder {folder_name} jest wykluczony")
                return []
            elif exclude_mode and folder_name not in excluded_folders:
                print(f"Błąd: wybrany folder {folder_name} nie znajduje się na liście wybranych.")
                self.search_manager.progress_queue.put(f"Błąd: folder {folder_name} nie jest wybrany")
                return []
            
            folders_to_search = [folder]
        
        return [f for f in folders_to_search if f is not None]
    
    def _collect_pdf_attachments(self, folders_to_search, date_from, date_to, 
                                seen_filenames, attachment_counter):
        """Collect all PDF attachments from specified folders."""
        from datetime import timezone
        # Ensure dates are timezone-aware
        if date_from and date_from.tzinfo is None:
            date_from = date_from.replace(tzinfo=timezone.utc)
        if date_to and date_to.tzinfo is None:
            date_to = date_to.replace(tzinfo=timezone.utc)
        all_attachments = []
        
        for folder in folders_to_search:
            if folder is None or self.search_manager.search_cancelled:
                continue
                
            folder_path = getattr(folder, "absolute", None) or (self.exchange_connection.get_folder_path(folder) if hasattr(self.exchange_connection, "get_folder_path") else str(folder))
            print(f"Przeszukuję folder: {folder_path}")
            self.search_manager.progress_queue.put(f"Skanowanie folderu: {folder_path}")
            
            try:
                # SERVER-SIDE FILTERING BY DATE (efficient)
                query = Q()
                if date_from:
                    query &= Q(datetime_received__gte=date_from)
                if date_to:
                    query &= Q(datetime_received__lt=date_to)

                for item in folder.all().filter(query).order_by("-datetime_received"):
                    if self.search_manager.search_cancelled:
                        break
                        
                    dt = item.datetime_received
                    print(f"Mail: '{item.subject}' ({dt}) | Zakres: {date_from} - {date_to}")

                    for att in item.attachments:
                        if self.search_manager.search_cancelled:
                            break
                        if att.name.lower().endswith(".pdf") and att.name not in seen_filenames:
                            attachment_counter += 1
                            all_attachments.append((att, item, folder_path, attachment_counter))
                            seen_filenames.add(att.name)
                            
            except Exception as e:
                print(f"Błąd przeszukiwania folderu {folder_path}: {e}")
                if ("Access is denied" in str(e) or
                    "cannot access System folder" in str(e) or
                    isinstance(e, errors.ErrorAccessDenied)):
                    with open("pdf_error.log", "a", encoding="utf-8") as logf:
                        logf.write(f"Folder pominięty przez błąd dostępu: {folder_path}\n{str(e)}\n{'-'*40}\n")
                    continue
                else:
                    print(f"Błąd w folderze {folder_path}: {e}")
        
        return all_attachments
    
    def _process_attachments_threaded(self, all_attachments, nip, seen_filenames):
        """Process PDF attachments using ThreadPoolExecutor."""
        total_attachments = len(all_attachments)
        if total_attachments == 0:
            self.search_manager.progress_queue.put("Nie znaleziono załączników PDF")
            return

        self.search_manager.progress_queue.put(f"Znaleziono {total_attachments} załączników PDF do przetworzenia")

        # Use ThreadPoolExecutor for PDF processing
        max_workers = min(4, total_attachments)  # Limit to 4 concurrent threads
        self.search_manager.search_executor = ThreadPoolExecutor(max_workers=max_workers)
        
        try:
            # Submit all PDF processing tasks
            future_to_attachment = {
                self.search_manager.search_executor.submit(
                    self.pdf_processor.process_pdf_attachment, 
                    att, item, folder_path, nip, seen_filenames, counter,
                    self.search_manager
                ): (att, item, folder_path, counter)
                for att, item, folder_path, counter in all_attachments
            }

            # Process completed tasks
            processed_count = 0
            for future in as_completed(future_to_attachment):
                if self.search_manager.search_cancelled:
                    break
                    
                processed_count += 1
                try:
                    result = future.result()
                    if result:
                        self.search_manager.result_queue.put(result)
                    
                    # Update progress
                    self.search_manager.progress_queue.put(
                        f"Przetworzono {processed_count}/{total_attachments} załączników"
                    )
                except Exception as e:
                    att, item, folder_path, counter = future_to_attachment[future]
                    print(f"Błąd przetwarzania załącznika {att.name}: {e}")

        finally:
            self.search_manager.search_executor.shutdown(wait=True)
            self.search_manager.search_executor = None