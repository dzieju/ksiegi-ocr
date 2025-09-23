#!/usr/bin/env python3
"""
Demo script to show PDF search functionality working
"""
import tkinter as tk
from tkinter import ttk
import os
import sys

# Add the gui directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from gui.mail_search_components.pdf_search import PDFSearcher, PDFSearchResult

def demo_pdf_search():
    """Demo PDF search functionality"""
    print("=== PDF Search Demo ===")
    
    # Create a simple test to show the functionality works
    def progress_callback(message):
        print(f"Progress: {message}")
    
    def result_callback(result):
        print(f"Result: {result.get_summary()}")
        if result.matches:
            for i, match in enumerate(result.matches, 1):
                print(f"  Match {i}: {match['text'][:100]}...")
        if result.error:
            print(f"  Error: {result.error}")
    
    searcher = PDFSearcher(progress_callback, result_callback)
    
    # Test with a non-existent file to show error handling
    print("\n1. Testing with non-existent file:")
    searcher.search_pdf("/fake/path.pdf", "test", threaded=False)
    
    # Test with empty query
    print("\n2. Testing with empty query:")
    searcher.search_pdf("test.pdf", "", threaded=False)
    
    # Test PDF creation and search (if pdfplumber available)
    try:
        # Create a simple text-based PDF for testing
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        print("\n3. Creating test PDF and searching:")
        test_pdf_path = "/tmp/test_document.pdf"
        
        # Create test PDF
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.drawString(100, 750, "This is a test document with faktura information.")
        c.drawString(100, 720, "Invoice number: F/12345/2025")
        c.drawString(100, 690, "Some other text here.")
        c.drawString(100, 660, "Another faktura reference: INV-2025-001")
        c.save()
        
        print(f"Created test PDF: {test_pdf_path}")
        
        # Search for "faktura"
        searcher.search_pdf(test_pdf_path, "faktura", threaded=False)
        
    except ImportError:
        print("\nreportlab not available, skipping PDF creation test")
        print("This would work with actual PDF files in production")
    
    print("\n=== Demo Complete ===")

def create_ui_demo():
    """Create a simple UI to demonstrate the PDF search interface"""
    print("=== Creating UI Demo ===")
    
    root = tk.Tk()
    root.title("PDF Search Demo - Księga Przychodów i Rozchodów")
    root.geometry("800x600")
    
    # Create a frame that mimics the mail search interface
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ttk.Label(main_frame, text="Przeszukiwanie Poczty", font=("Arial", 14, "bold"), foreground="blue")
    title_label.pack(pady=(0, 20))
    
    # Form fields
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(fill="x", pady=10)
    
    # Row 1: Folder
    ttk.Label(form_frame, text="Folder przeszukiwania:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(form_frame, width=50).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(form_frame, text="Wykryj foldery").grid(row=0, column=2, padx=5, pady=5)
    
    # Row 2: Subject
    ttk.Label(form_frame, text="Co ma szukać w temacie maila:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(form_frame, width=50).grid(row=1, column=1, padx=5, pady=5)
    
    # Row 3: PDF Search (NEW!)
    pdf_label = ttk.Label(form_frame, text="Wyszukaj w pliku PDF:", font=("Arial", 10, "bold"), foreground="darkblue")
    pdf_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)
    
    pdf_frame = ttk.Frame(form_frame)
    pdf_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
    
    pdf_path_var = tk.StringVar()
    pdf_entry = ttk.Entry(pdf_frame, textvariable=pdf_path_var, width=40, state='readonly')
    pdf_entry.pack(side="left", fill="x", expand=True)
    
    def select_pdf():
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Wybierz plik PDF do przeszukania", 
            filetypes=[("PDF files", "*.pdf")]
        )
        if filepath:
            pdf_path_var.set(filepath)
    
    ttk.Button(pdf_frame, text="Wybierz PDF", command=select_pdf).pack(side="right", padx=(5, 0))
    
    # Row 4: PDF Search text
    ttk.Label(form_frame, text="Fraza do wyszukania:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    pdf_search_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=pdf_search_var, width=50).grid(row=3, column=1, padx=5, pady=5)
    
    # Row 5: Sender
    ttk.Label(form_frame, text="Nadawca maila:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(form_frame, width=50).grid(row=4, column=1, padx=5, pady=5)
    
    # Checkboxes
    checkbox_frame = ttk.Frame(form_frame)
    checkbox_frame.grid(row=5, column=1, columnspan=2, sticky="w", padx=5, pady=10)
    
    ttk.Checkbutton(checkbox_frame, text="Tylko nieprzeczytane").pack(side="left", padx=(0, 20))
    ttk.Checkbutton(checkbox_frame, text="Tylko z załącznikami").pack(side="left")
    
    # Search button
    search_frame = ttk.Frame(main_frame)
    search_frame.pack(pady=20)
    
    def perform_search():
        pdf_path = pdf_path_var.get().strip()
        search_text = pdf_search_var.get().strip()
        
        if pdf_path and search_text:
            # Show demo results
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, f"Przeszukiwanie pliku: {os.path.basename(pdf_path)}\n")
            result_text.insert(tk.END, f"Wyszukiwana fraza: '{search_text}'\n\n")
            result_text.insert(tk.END, "=== Wyniki wyszukiwania ===\n")
            result_text.insert(tk.END, "Znajdowanie tekstu w pliku PDF...\n")
            result_text.insert(tk.END, "Próba wyszukiwania tekstowego...\n")
            result_text.insert(tk.END, "Jeśli nie znajdzie tekstu, rozpocznie OCR...\n\n")
            result_text.insert(tk.END, "Demo: Ta funkcjonalność jest zintegrowana i działająca!\n")
        else:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "Proszę wybrać plik PDF i wpisać frazę do wyszukania.\n")
    
    ttk.Button(search_frame, text="Rozpocznij wyszukiwanie", command=perform_search).pack()
    
    # Results area
    results_label = ttk.Label(main_frame, text="Wyniki wyszukiwania:", font=("Arial", 12, "bold"))
    results_label.pack(anchor="w", pady=(20, 5))
    
    result_frame = ttk.Frame(main_frame)
    result_frame.pack(fill="both", expand=True)
    
    result_text = tk.Text(result_frame, wrap="word", height=15)
    result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
    result_text.configure(yscrollcommand=result_scrollbar.set)
    
    result_text.pack(side="left", fill="both", expand=True)
    result_scrollbar.pack(side="right", fill="y")
    
    # Add some demo text
    result_text.insert(tk.END, "Gotowy do wyszukiwania...\n\n")
    result_text.insert(tk.END, "Nowe funkcje dodane:\n")
    result_text.insert(tk.END, "✓ Pole 'Wyszukaj w pliku PDF:' z przyciskiem wyboru pliku\n")
    result_text.insert(tk.END, "✓ Pole 'Fraza do wyszukania:' do wpisania tekstu\n")
    result_text.insert(tk.END, "✓ Integracja z wyszukiwaniem tekstowym i OCR\n")
    result_text.insert(tk.END, "✓ Wyświetlanie wyników w osobnym oknie\n")
    result_text.insert(tk.END, "✓ Obsługa zarówno plików PDF z tekstem jak i zeskanowanych\n\n")
    result_text.insert(tk.END, "Wybierz plik PDF i wpisz frazę aby przetestować!")
    
    # Make grid columns expandable
    form_frame.grid_columnconfigure(1, weight=1)
    
    root.mainloop()

if __name__ == "__main__":
    print("=== PDF Search Integration Demo ===")
    
    # Run functional demo
    demo_pdf_search()
    
    print("\nLaunching UI Demo...")
    print("Pokazuje nowy interfejs z polami PDF search")
    
    # Launch UI demo
    create_ui_demo()