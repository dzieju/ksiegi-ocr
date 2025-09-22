"""
Results display handler for mail search functionality
"""
import tkinter as tk


class ResultsDisplay:
    """Handles display of search results"""
    
    def __init__(self, results_area):
        self.results_area = results_area
    
    def display_results(self, results):
        """Display search results in the text area"""
        self.results_area.delete("1.0", tk.END)
        
        if not results:
            self.results_area.insert(tk.END, "Nie znaleziono żadnych wiadomości spełniających kryteria.\n")
            return
            
        # Header
        header = f"{'Data':<20} | {'Nadawca':<30} | {'Temat':<50} | {'Status':<12} | {'Załączniki':<10}"
        self.results_area.insert(tk.END, header + "\n")
        self.results_area.insert(tk.END, "-" * len(header) + "\n")
        
        # Results
        for result in results:
            date_str = result['datetime_received'].strftime('%Y-%m-%d %H:%M') if result['datetime_received'] else 'Brak daty'
            sender = result['sender'][:28] if len(result['sender']) > 28 else result['sender']
            subject = result['subject'][:48] if len(result['subject']) > 48 else result['subject']
            status = "Nieprzeczyt." if not result['is_read'] else "Przeczytane"
            attachments = f"{result['attachment_count']}" if result['has_attachments'] else "Brak"
            
            line = f"{date_str:<20} | {sender:<30} | {subject:<50} | {status:<12} | {attachments:<10}"
            self.results_area.insert(tk.END, line + "\n")
    
    def clear_results(self):
        """Clear the results area"""
        self.results_area.delete("1.0", tk.END)
    
    def show_status(self, message):
        """Show status message in results area"""
        self.results_area.delete("1.0", tk.END)
        self.results_area.insert(tk.END, message + "\n")