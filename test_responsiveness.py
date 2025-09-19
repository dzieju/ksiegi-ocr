#!/usr/bin/env python3
"""
Test script to validate responsiveness improvements in Księgi tab.
Tests the threading functionality without GUI dependencies.
"""

import sys
import os
import time
import tempfile

# Add the project root to Python path
sys.path.insert(0, '/home/runner/work/ksiegi-ocr/ksiegi-ocr')

def test_threading_infrastructure():
    """Test that threading infrastructure is properly implemented."""
    try:
        from ocr.ksiegi_processor import KsiegiProcessor, OCRTaskManager
        
        # Test OCR task manager creation
        processor = KsiegiProcessor()
        task_manager = processor.task_manager
        
        print("✅ Threading infrastructure initialized successfully")
        
        # Test queue operations
        task_manager.progress_queue.put("Test progress message")
        task_manager.result_queue.put({"type": "test", "data": "test_data"})
        
        progress_updates = task_manager.get_progress_updates()
        results = task_manager.get_results()
        
        assert len(progress_updates) == 1
        assert len(results) == 1
        assert progress_updates[0] == "Test progress message"
        assert results[0]["type"] == "test"
        
        print("✅ Queue communication working correctly")
        
        # Test task state tracking
        assert not task_manager.is_task_active()
        print("✅ Task state tracking working")
        
        return True
        
    except Exception as e:
        print(f"❌ Threading infrastructure test failed: {e}")
        return False

def test_threaded_operations_simulation():
    """Simulate threaded operations to test responsiveness patterns."""
    try:
        from ocr.ksiegi_processor import KsiegiProcessor
        import threading
        import queue
        
        processor = KsiegiProcessor()
        
        # Simulate CSV comparison threading pattern
        def mock_csv_comparison():
            """Mock CSV comparison that sends progress updates."""
            for i in range(5):
                processor.task_manager.progress_queue.put(f"Processing step {i+1}/5")
                time.sleep(0.1)  # Simulate work
                
            processor.task_manager.result_queue.put({
                'type': 'csv_comparison_result',
                'status': 'completed'
            })
        
        # Start mock task
        thread = processor.task_manager.start_task(mock_csv_comparison)
        
        # Collect progress updates
        start_time = time.time()
        progress_messages = []
        results = []
        
        while time.time() - start_time < 2.0:  # Wait up to 2 seconds
            progress = processor.task_manager.get_progress_updates()
            result = processor.task_manager.get_results()
            
            progress_messages.extend(progress)
            results.extend(result)
            
            time.sleep(0.05)  # Simulate GUI polling interval
            
            if any(r.get('type') == 'csv_comparison_result' for r in results):
                break
        
        thread.join(timeout=1.0)
        
        print(f"✅ Received {len(progress_messages)} progress updates")
        print(f"✅ Received {len(results)} results")
        
        assert len(progress_messages) == 5
        assert len(results) == 1
        assert results[0]['type'] == 'csv_comparison_result'
        
        print("✅ Threaded operation simulation successful")
        return True
        
    except Exception as e:
        print(f"❌ Threaded operation simulation failed: {e}")
        return False

def test_folder_processing_pattern():
    """Test folder processing responsiveness pattern."""
    try:
        from ocr.ksiegi_processor import KsiegiProcessor
        import threading
        
        processor = KsiegiProcessor()
        
        # Create a temporary directory with some files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some mock PDF files
            for i in range(10):
                with open(os.path.join(temp_dir, f"file_{i}.pdf"), 'w') as f:
                    f.write("mock pdf content")
            
            # Create some non-PDF files that should be ignored
            with open(os.path.join(temp_dir, "readme.txt"), 'w') as f:
                f.write("readme content")
                
            with open(os.path.join(temp_dir, ".hidden.pdf"), 'w') as f:
                f.write("hidden pdf")
            
            def mock_folder_processing():
                """Mock folder processing with progress updates."""
                all_items = os.listdir(temp_dir)
                total_items = len(all_items)
                
                processor.task_manager.progress_queue.put(f"Processing {total_items} items...")
                
                pdf_files = []
                processed = 0
                
                for item in all_items:
                    if (os.path.isfile(os.path.join(temp_dir, item)) and 
                        not item.startswith('.') and 
                        item.lower().endswith('.pdf')):
                        pdf_files.append(os.path.splitext(item)[0])
                    
                    processed += 1
                    if processed % 5 == 0 or processed == total_items:
                        processor.task_manager.progress_queue.put(
                            f"Processed {processed}/{total_items}, found {len(pdf_files)} PDFs"
                        )
                
                processor.task_manager.result_queue.put({
                    'type': 'folder_processing_result',
                    'success': True,
                    'file_count': len(pdf_files)
                })
            
            # Start mock task
            thread = processor.task_manager.start_task(mock_folder_processing)
            
            # Collect results
            start_time = time.time()
            progress_messages = []
            results = []
            
            while time.time() - start_time < 2.0:
                progress = processor.task_manager.get_progress_updates()
                result = processor.task_manager.get_results()
                
                progress_messages.extend(progress)
                results.extend(result)
                
                time.sleep(0.05)
                
                if any(r.get('type') == 'folder_processing_result' for r in results):
                    break
            
            thread.join(timeout=1.0)
            
            print(f"✅ Folder processing: {len(progress_messages)} progress updates")
            assert len(results) == 1
            assert results[0]['type'] == 'folder_processing_result'
            assert results[0]['success'] == True
            assert results[0]['file_count'] == 10  # Should find 10 PDF files
            
            print("✅ Folder processing pattern working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Folder processing pattern test failed: {e}")
        return False

def main():
    """Run all responsiveness tests."""
    print("🔧 Testing responsiveness improvements in Księgi tab...")
    print("=" * 60)
    
    tests = [
        ("Threading Infrastructure", test_threading_infrastructure),
        ("Threaded Operations Simulation", test_threaded_operations_simulation),
        ("Folder Processing Pattern", test_folder_processing_pattern),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Responsiveness Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All responsiveness tests passed! GUI should remain responsive during operations.")
        return 0
    else:
        print("⚠️  Some responsiveness tests failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())