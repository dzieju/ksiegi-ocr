#!/usr/bin/env python3
"""
Demo script showing responsiveness improvements in Księgi tab.
Simulates GUI operations without requiring GUI dependencies.
"""

import sys
import time
import threading
import tempfile
import os

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/ksiegi-ocr/ksiegi-ocr')

def demo_responsive_csv_comparison():
    """Demo of responsive CSV comparison."""
    print("🔄 Demo: Responsive CSV Comparison")
    print("-" * 40)
    
    from ocr.ksiegi_processor import KsiegiProcessor
    
    processor = KsiegiProcessor()
    
    def mock_csv_comparison():
        """Mock CSV comparison with realistic progress updates."""
        steps = [
            "Wykrywanie delimitatorów CSV...",
            "Odczytywanie plików CSV...",
            "Przetwarzanie kolumny C...",
            "Wykonywanie porównania...",
            "Zapisywanie wyników...",
            "Formatowanie wyników..."
        ]
        
        for i, step in enumerate(steps):
            processor.task_manager.progress_queue.put(step)
            time.sleep(0.3)  # Simulate processing time
            
        processor.task_manager.result_queue.put({
            'type': 'csv_comparison_result',
            'status': 'completed',
            'comparison_text': "=== PORÓWNANIE CSV UKOŃCZONE ===\n• Identyczne: 150\n• Różne: 25\n• Tylko w pliku 1: 10\n• Tylko w pliku 2: 5"
        })
    
    # Start task
    thread = processor.task_manager.start_task(mock_csv_comparison)
    
    print("📊 Starting CSV comparison task...")
    print("💡 GUI would remain responsive while showing these updates:")
    print()
    
    # Simulate GUI polling for updates
    start_time = time.time()
    while time.time() - start_time < 3.0:
        # Get progress updates (like GUI would every 50ms)
        progress_updates = processor.task_manager.get_progress_updates()
        for update in progress_updates:
            print(f"   📢 Status: {update}")
        
        # Check for results
        results = processor.task_manager.get_results()
        for result in results:
            if result['type'] == 'csv_comparison_result':
                print(f"   ✅ Task completed!")
                print(f"   📋 Results: {result['comparison_text']}")
                thread.join()
                return
        
        time.sleep(0.05)  # Simulate GUI event loop
    
    thread.join(timeout=1.0)
    print("   ✅ Demo completed!\n")

def demo_responsive_folder_processing():
    """Demo of responsive folder processing."""
    print("🔄 Demo: Responsive Folder Processing")
    print("-" * 40)
    
    from ocr.ksiegi_processor import KsiegiProcessor
    
    processor = KsiegiProcessor()
    
    # Create temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock files
        files_created = []
        for i in range(50):  # Simulate larger folder
            filename = f"document_{i:03d}.pdf"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"Mock PDF content {i}")
            files_created.append(filename)
        
        # Add some non-PDF files
        for ext in ['txt', 'doc', 'jpg']:
            filepath = os.path.join(temp_dir, f"other_file.{ext}")
            with open(filepath, 'w') as f:
                f.write("Non-PDF content")
        
        def mock_folder_processing():
            """Mock folder processing with progress updates."""
            all_items = os.listdir(temp_dir)
            total_items = len(all_items)
            
            processor.task_manager.progress_queue.put(f"Skanowanie {total_items} plików...")
            
            pdf_files = []
            processed_count = 0
            
            for item in all_items:
                # Simulate processing time
                time.sleep(0.02)
                
                if (os.path.isfile(os.path.join(temp_dir, item)) and 
                    not item.startswith('.') and 
                    item.lower().endswith('.pdf')):
                    pdf_files.append(os.path.splitext(item)[0])
                
                processed_count += 1
                
                # Progress updates every 10 files
                if processed_count % 10 == 0 or processed_count == total_items:
                    processor.task_manager.progress_queue.put(
                        f"Przetworzono {processed_count}/{total_items}, znaleziono {len(pdf_files)} plików PDF"
                    )
            
            processor.task_manager.progress_queue.put("Zapisywanie wyników CSV...")
            time.sleep(0.2)  # Simulate CSV writing
            
            processor.task_manager.result_queue.put({
                'type': 'folder_processing_result',
                'success': True,
                'file_count': len(pdf_files),
                'csv_filename': 'test_folder.csv'
            })
        
        # Start task
        thread = processor.task_manager.start_task(mock_folder_processing)
        
        print(f"📁 Processing folder with {len(files_created)} PDF files...")
        print("💡 GUI would remain responsive while showing these updates:")
        print()
        
        # Simulate GUI polling
        start_time = time.time()
        while time.time() - start_time < 5.0:
            progress_updates = processor.task_manager.get_progress_updates()
            for update in progress_updates:
                print(f"   📢 Status: {update}")
            
            results = processor.task_manager.get_results()
            for result in results:
                if result['type'] == 'folder_processing_result':
                    print(f"   ✅ Folder processing completed!")
                    print(f"   📊 Found {result['file_count']} PDF files")
                    print(f"   💾 Saved to {result['csv_filename']}")
                    thread.join()
                    return
            
            time.sleep(0.05)
        
        thread.join(timeout=1.0)
        print("   ✅ Demo completed!\n")

def demo_responsive_cell_ocr():
    """Demo of responsive cell OCR processing."""
    print("🔄 Demo: Responsive Cell OCR Processing")
    print("-" * 40)
    
    from ocr.ksiegi_processor import KsiegiProcessor
    
    processor = KsiegiProcessor()
    
    def mock_cell_ocr():
        """Mock OCR processing of cells with progress updates."""
        total_cells = 25
        processor.task_manager.progress_queue.put(f"Przetwarzanie {total_cells} komórek OCR...")
        
        for i in range(total_cells):
            # Simulate OCR processing time
            time.sleep(0.1)
            
            # Send individual cell result
            processor.task_manager.result_queue.put({
                'type': 'cell_result',
                'x': 100 + i * 20,
                'y': 200 + i * 15,
                'text': f'F/12345/01/{i:02d}/M1'
            })
            
            # Progress updates every 5 cells
            if (i + 1) % 5 == 0:
                processor.task_manager.progress_queue.put(
                    f"OCR komórek: {i + 1}/{total_cells}"
                )
        
        processor.task_manager.result_queue.put({
            'type': 'all_cells_complete',
            'processed_count': total_cells
        })
    
    # Start task
    thread = processor.task_manager.start_task(mock_cell_ocr)
    
    print("🔍 Starting OCR processing of all cells...")
    print("💡 GUI would show real-time results as cells are processed:")
    print()
    
    # Simulate GUI polling
    start_time = time.time()
    cell_results_shown = 0
    
    while time.time() - start_time < 4.0:
        progress_updates = processor.task_manager.get_progress_updates()
        for update in progress_updates:
            print(f"   📢 Status: {update}")
        
        results = processor.task_manager.get_results()
        for result in results:
            if result['type'] == 'cell_result':
                cell_results_shown += 1
                if cell_results_shown <= 5:  # Show first few results
                    print(f"   🔍 Cell OCR: x={result['x']} y={result['y']} → {result['text']}")
                elif cell_results_shown == 6:
                    print("   ... (showing additional results in real-time)")
            elif result['type'] == 'all_cells_complete':
                print(f"   ✅ All cells processed! Total: {result['processed_count']}")
                thread.join()
                return
        
        time.sleep(0.05)
    
    thread.join(timeout=1.0)
    print("   ✅ Demo completed!\n")

def main():
    """Run all responsiveness demos."""
    print("🎯 Księgi Tab Responsiveness Demonstrations")
    print("=" * 60)
    print()
    print("These demos show how the GUI remains responsive during:")
    print("• Large CSV file comparisons")
    print("• Folder processing with many files")
    print("• OCR processing of multiple cells")
    print()
    print("In a real GUI, users can cancel operations and see real-time progress.")
    print("=" * 60)
    print()
    
    demo_responsive_csv_comparison()
    demo_responsive_folder_processing() 
    demo_responsive_cell_ocr()
    
    print("🎉 All responsiveness demonstrations completed!")
    print("💡 The GUI will now remain responsive during all these operations.")

if __name__ == "__main__":
    main()