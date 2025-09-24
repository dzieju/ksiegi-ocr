#!/usr/bin/env python3
"""
System requirements detection module for ksiegi-ocr application.

This module provides functions to check the availability and status
of all required system components and dependencies.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class SystemRequirementsChecker:
    """Checks system requirements and provides status information."""
    
    def __init__(self):
        """Initialize the requirements checker."""
        self.requirements = {
            'tkinter': {'status': False, 'description': 'GUI framework', 'error': None},
            'poppler': {'status': False, 'description': 'PDF processing tools', 'error': None},
            'tesseract': {'status': False, 'description': 'OCR engine (Tesseract)', 'error': None},
            'easyocr': {'status': False, 'description': 'OCR engine (EasyOCR)', 'error': None},
            'paddleocr': {'status': False, 'description': 'OCR engine (PaddleOCR)', 'error': None},
            'python_deps': {'status': False, 'description': 'Python dependencies', 'error': None},
        }
        
    def check_all_requirements(self) -> Dict[str, Dict]:
        """Check all system requirements and return status."""
        self._check_tkinter()
        self._check_poppler()
        self._check_tesseract()
        self._check_easyocr()
        self._check_paddleocr()
        self._check_python_dependencies()
        
        return self.requirements
    
    def _check_tkinter(self):
        """Check if tkinter is available."""
        try:
            import tkinter
            self.requirements['tkinter']['status'] = True
        except ImportError as e:
            self.requirements['tkinter']['error'] = str(e)
    
    def _check_poppler(self):
        """Check if Poppler is available."""
        try:
            # Try to import poppler_utils module
            from tools.poppler_utils import PopplerManager
            manager = PopplerManager()
            
            if manager.is_detected:
                self.requirements['poppler']['status'] = True
            else:
                self.requirements['poppler']['error'] = manager.detection_error or "Poppler not detected"
        except Exception as e:
            self.requirements['poppler']['error'] = str(e)
    
    def _check_tesseract(self):
        """Check if Tesseract OCR is available."""
        try:
            # Check if tesseract command is available
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.requirements['tesseract']['status'] = True
            else:
                self.requirements['tesseract']['error'] = "Tesseract command failed"
        except FileNotFoundError:
            self.requirements['tesseract']['error'] = "Tesseract not found in PATH"
        except subprocess.TimeoutExpired:
            self.requirements['tesseract']['error'] = "Tesseract command timeout"
        except Exception as e:
            self.requirements['tesseract']['error'] = str(e)
    
    def _check_easyocr(self):
        """Check if EasyOCR is available."""
        try:
            import easyocr
            self.requirements['easyocr']['status'] = True
        except ImportError:
            self.requirements['easyocr']['error'] = "EasyOCR module not installed"
        except Exception as e:
            self.requirements['easyocr']['error'] = str(e)
    
    def _check_paddleocr(self):
        """Check if PaddleOCR is available."""
        try:
            import paddleocr
            self.requirements['paddleocr']['status'] = True
        except ImportError:
            self.requirements['paddleocr']['error'] = "PaddleOCR module not installed"
        except Exception as e:
            self.requirements['paddleocr']['error'] = str(e)
    
    def _check_python_dependencies(self):
        """Check Python dependencies from requirements.txt."""
        try:
            requirements_file = Path(__file__).parent.parent / "requirements.txt"
            if not requirements_file.exists():
                self.requirements['python_deps']['error'] = "requirements.txt not found"
                return
            
            # Read requirements and check each one
            missing_deps = []
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before any version specifiers)
                        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('<')[0].split('>')[0].split('~')[0].strip()
                        try:
                            importlib.import_module(package_name.replace('-', '_'))
                        except ImportError:
                            missing_deps.append(package_name)
            
            if not missing_deps:
                self.requirements['python_deps']['status'] = True
            else:
                self.requirements['python_deps']['error'] = f"Missing: {', '.join(missing_deps[:3])}{'...' if len(missing_deps) > 3 else ''}"
                
        except Exception as e:
            self.requirements['python_deps']['error'] = str(e)
    
    def get_summary(self) -> Tuple[int, int]:
        """Get summary of requirements status."""
        total = len(self.requirements)
        passed = sum(1 for req in self.requirements.values() if req['status'])
        return passed, total
    
    def get_diagnostics(self) -> Dict[str, str]:
        """Get diagnostic information for troubleshooting."""
        diagnostics = {}
        
        # Python version
        diagnostics['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Platform
        diagnostics['platform'] = sys.platform
        
        # Working directory
        diagnostics['working_dir'] = str(Path.cwd())
        
        # PATH environment
        path_env = os.environ.get('PATH', '')
        diagnostics['path_length'] = len(path_env.split(os.pathsep))
        
        return diagnostics


# Convenience functions for quick checks
def check_all_requirements() -> Dict[str, Dict]:
    """Quick function to check all requirements."""
    checker = SystemRequirementsChecker()
    return checker.check_all_requirements()


def get_requirements_summary() -> Tuple[int, int]:
    """Quick function to get requirements summary."""
    checker = SystemRequirementsChecker()
    checker.check_all_requirements()
    return checker.get_summary()


def get_system_diagnostics() -> Dict[str, str]:
    """Quick function to get system diagnostics."""
    checker = SystemRequirementsChecker()
    return checker.get_diagnostics()


if __name__ == "__main__":
    # Command line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Check system requirements for ksiegi-ocr")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--diagnostics", "-d", action="store_true", help="Show diagnostics")
    
    args = parser.parse_args()
    
    checker = SystemRequirementsChecker()
    requirements = checker.check_all_requirements()
    
    print("System Requirements Check")
    print("=" * 40)
    
    for name, info in requirements.items():
        status_icon = "✅" if info['status'] else "❌"
        print(f"{status_icon} {name.title()}: {info['description']}")
        if not info['status'] and info['error']:
            print(f"   Error: {info['error']}")
        if args.verbose and info['status']:
            print(f"   OK")
    
    passed, total = checker.get_summary()
    print(f"\nSummary: {passed}/{total} requirements met")
    
    if args.diagnostics:
        print("\nDiagnostics:")
        print("-" * 20)
        diagnostics = checker.get_diagnostics()
        for key, value in diagnostics.items():
            print(f"{key}: {value}")