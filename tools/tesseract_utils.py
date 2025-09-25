#!/usr/bin/env python3
"""
Tesseract utilities for automated detection and PATH configuration.

This module provides automatic detection of Tesseract OCR installation
and configuration for pytesseract across different platforms.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class TesseractManager:
    """Manager for Tesseract OCR integration."""
    
    def __init__(self):
        """Initialize TesseractManager."""
        self.tesseract_path = None
        self.is_detected = False
        self.detection_error = None
        
        # Detect tesseract on initialization
        self._detect_tesseract()
    
    def _detect_tesseract(self) -> bool:
        """
        Detect tesseract installation and configure paths.
        
        Returns:
            bool: True if tesseract was successfully detected and configured.
        """
        try:
            # First, check if tesseract is in system PATH
            tesseract_in_path = shutil.which("tesseract")
            if tesseract_in_path:
                self.tesseract_path = tesseract_in_path
                self.is_detected = True
                self._configure_pytesseract()
                return True
            
            # If not in PATH, check common Windows locations
            common_windows_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
            
            for path_str in common_windows_paths:
                path = Path(path_str)
                if path.exists() and self._validate_tesseract_path(path):
                    self.tesseract_path = str(path)
                    self.is_detected = True
                    self._configure_pytesseract()
                    return True
            
            # If no valid tesseract found
            self.detection_error = f"Tesseract not found in PATH or common locations: {common_windows_paths}"
            return False
            
        except Exception as e:
            self.detection_error = f"Error during tesseract detection: {e}"
            return False
    
    def _validate_tesseract_path(self, tesseract_path: Path) -> bool:
        """
        Validate that tesseract_path points to a valid tesseract executable.
        
        Args:
            tesseract_path: Path to validate
            
        Returns:
            bool: True if path points to valid tesseract executable
        """
        try:
            if not tesseract_path.exists():
                return False
            
            # Try to run tesseract --version to validate
            if sys.platform.startswith("win") or tesseract_path.suffix == "":
                # On Windows or if it's an executable without extension
                result = subprocess.run(
                    [str(tesseract_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            else:
                # On non-Windows, if it's a .exe file, just check if it exists and has reasonable size
                return tesseract_path.is_file() and tesseract_path.stat().st_size > 1000
                
        except Exception:
            return False
    
    def _configure_pytesseract(self) -> None:
        """Configure pytesseract to use the detected tesseract path."""
        if self.tesseract_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            except ImportError:
                # pytesseract not available, but we still record the path for later use
                pass
    
    def get_tesseract_path(self) -> Optional[str]:
        """
        Get the detected tesseract path for use by other modules.
        
        Returns:
            String path to tesseract executable, or None if not detected
        """
        return self.tesseract_path
    
    def get_status(self) -> Dict[str, any]:
        """Get detailed status information about tesseract detection."""
        return {
            "detected": self.is_detected,
            "tesseract_path": self.tesseract_path,
            "error": self.detection_error,
            "version": self._get_version() if self.is_detected else None
        }
    
    def _get_version(self) -> Optional[str]:
        """Get tesseract version information."""
        if not self.tesseract_path:
            return None
        
        try:
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Tesseract outputs version to stderr, extract first line
                version_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                version_line = version_output.split('\n')[0] if version_output else ''
                return version_line
            
        except Exception:
            pass
        
        return None
    
    def test_tesseract(self) -> Tuple[bool, str]:
        """
        Test if tesseract is working properly.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_detected:
            return False, "Tesseract not detected"
        
        try:
            version = self._get_version()
            if version:
                return True, f"Tesseract working properly: {version}"
            else:
                return False, "Tesseract found but version check failed"
                
        except Exception as e:
            return False, f"Error testing tesseract: {str(e)}"
    
    def print_status(self) -> None:
        """Print detailed tesseract status to console."""
        status = self.get_status()
        
        print(f"\n🔍 TESSERACT STATUS")
        print("=" * 30)
        
        if status["detected"]:
            print(f"✅ Tesseract detected: {status['tesseract_path']}")
            if status["version"]:
                print(f"📦 Version: {status['version']}")
            
            # Test if it's working
            success, message = self.test_tesseract()
            if success:
                print(f"✅ Test: {message}")
            else:
                print(f"❌ Test failed: {message}")
                
        else:
            print(f"❌ Tesseract not detected")
            if status["error"]:
                print(f"💬 Error: {status['error']}")


# Global instance for easy access
_tesseract_manager = None


def get_tesseract_manager() -> TesseractManager:
    """Get the global TesseractManager instance."""
    global _tesseract_manager
    if _tesseract_manager is None:
        _tesseract_manager = TesseractManager()
    return _tesseract_manager


def detect_tesseract() -> bool:
    """
    Quick tesseract detection function.
    
    Returns:
        bool: True if tesseract is detected and configured
    """
    return get_tesseract_manager().is_detected


def print_tesseract_status() -> None:
    """Print tesseract status to console."""
    get_tesseract_manager().print_status()


def get_tesseract_path() -> Optional[str]:
    """
    Get the detected tesseract path for use by other modules.
    
    Returns:
        String path to tesseract executable, or None if not detected
    """
    return get_tesseract_manager().get_tesseract_path()


def configure_pytesseract() -> bool:
    """
    Configure pytesseract to use auto-detected tesseract path.
    
    Returns:
        bool: True if successfully configured, False otherwise
    """
    manager = get_tesseract_manager()
    if manager.is_detected:
        manager._configure_pytesseract()
        return True
    return False


def test_tesseract_startup() -> Tuple[bool, str]:
    """
    Test tesseract integration on startup.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    manager = get_tesseract_manager()
    if manager.is_detected:
        return manager.test_tesseract()
    else:
        error_msg = manager.detection_error or "Unknown error"
        return False, f"Tesseract not detected: {error_msg}"


if __name__ == "__main__":
    # Command line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Tesseract utilities manager")
    parser.add_argument("--status", action="store_true", help="Show tesseract status")
    parser.add_argument("--test", action="store_true", help="Test tesseract functionality")
    parser.add_argument("--path", action="store_true", help="Show tesseract path only")
    
    args = parser.parse_args()
    
    if args.path:
        path = get_tesseract_path()
        if path:
            print(path)
        else:
            print("Tesseract not detected")
            sys.exit(1)
    elif args.test:
        success, message = test_tesseract_startup()
        print(message)
        sys.exit(0 if success else 1)
    else:
        # Default: show status
        print_tesseract_status()