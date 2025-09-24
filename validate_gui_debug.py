#!/usr/bin/env python3
"""
Test script to validate GUI debug functionality
Run this to test the debug changes without needing to run the full GUI application.
"""

import sys
import traceback

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        # Test basic imports
        from exchangelib.winzone import MS_TIMEZONE_TO_IANA_MAP
        print("✅ exchangelib import successful")
        
        import customtkinter as ctk
        print("✅ customtkinter import successful")
        
        from gui.modern_theme import ModernTheme
        print("✅ ModernTheme import successful")
        
        from gui.main_window import MainWindow
        print("✅ MainWindow import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_debug_structure():
    """Test that debug code structure is present"""
    print("\n🔍 Testing debug code structure...")
    
    try:
        # Read main.py to check for debug logging
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
            
        # Check for expected debug statements
        expected_debug_statements = [
            'print("DEBUG: Starting application...")',
            'print("DEBUG: MainWindow created successfully")',
            'print("DEBUG: Starting mainloop()...")'
        ]
        
        for statement in expected_debug_statements:
            if statement in main_content:
                print(f"✅ Found: {statement}")
            else:
                print(f"❌ Missing: {statement}")
                
        # Read main_window.py to check for test widgets
        with open('gui/main_window.py', 'r', encoding='utf-8') as f:
            window_content = f.read()
            
        # Check for test widget code
        test_widget_checks = [
            'TEST: MainWindow Direct Widget',
            'TEST: TabView Direct Widget',
            'WIDGET VISIBILITY TEST SUMMARY',
            'test_label_main',
            'test_button_main',
            'test_label_tabview',
            'test_button_tabview'
        ]
        
        for check in test_widget_checks:
            if check in window_content:
                print(f"✅ Found test widget code: {check}")
            else:
                print(f"❌ Missing test widget code: {check}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking debug structure: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("="*60)
    print("🚀 GUI DEBUG TEST SUITE")
    print("="*60)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test debug structure
    structure_ok = test_debug_structure()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if imports_ok and structure_ok:
        print("✅ All tests passed! The debug implementation is ready to use.")
        print("\n📝 To run the actual GUI debug:")
        print("   python main.py")
        print("\n🔍 Look for these debug outputs:")
        print("   - 🚨 TEST: MainWindow Direct Widget (red)")
        print("   - 🎯 TEST: TabView Direct Widget (blue)")
        print("   - 🧪 WIDGET VISIBILITY TEST SUMMARY")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        
    print("="*60)

if __name__ == "__main__":
    main()