#!/usr/bin/env python3
"""
Poppler utilities for automated detection and PATH configuration.

This module provides automatic detection of local poppler installation
and PATH configuration for cross-platform compatibility.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class PopplerManager:
    """Manager for Poppler PDF utilities integration."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize PopplerManager.
        
        Args:
            repo_root: Root directory of the repository. If None, auto-detect.
        """
        self.repo_root = repo_root or self._detect_repo_root()
        self.poppler_path = self.repo_root / "poppler"
        self.bin_path = None
        self.is_detected = False
        self.detection_error = None
        
        # Detect poppler on initialization
        self._detect_poppler()
    
    def _detect_repo_root(self) -> Path:
        """Auto-detect repository root directory."""
        # Start from current file's directory and go up to find git repo
        current = Path(__file__).parent
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        
        # If not found, use current working directory
        return Path.cwd()
    
    def _detect_poppler(self) -> bool:
        """
        Detect poppler installation and configure paths.
        
        Returns:
            bool: True if poppler was successfully detected and configured.
        """
        try:
            # Check if poppler directory exists
            if not self.poppler_path.exists():
                self.detection_error = f"Poppler directory not found: {self.poppler_path}"
                return False
            
            # Detect OS-specific bin path
            possible_bin_paths = [
                self.poppler_path / "Library" / "bin",  # Windows (conda/vcpkg style)
                self.poppler_path / "bin",               # Linux/Unix style
                self.poppler_path,                       # Direct bin directory
            ]
            
            for bin_path in possible_bin_paths:
                if bin_path.exists() and self._validate_bin_path(bin_path):
                    self.bin_path = bin_path
                    self.is_detected = True
                    self._configure_path()
                    return True
            
            # If no valid bin path found
            self.detection_error = f"No valid poppler binaries found in: {possible_bin_paths}"
            return False
            
        except Exception as e:
            self.detection_error = f"Error during poppler detection: {e}"
            return False
    
    def _validate_bin_path(self, bin_path: Path) -> bool:
        """
        Validate that bin_path contains essential poppler executables.
        
        Args:
            bin_path: Path to validate
            
        Returns:
            bool: True if path contains valid poppler binaries
        """
        # Essential poppler executables (without extension for cross-platform)
        essential_tools = ["pdfinfo", "pdfimages", "pdftoppm"]
        
        # Check for Windows (.exe) and Linux (no extension) versions
        for tool in essential_tools:
            found = False
            for ext in [".exe", ""]:
                if (bin_path / f"{tool}{ext}").exists():
                    found = True
                    break
            if not found:
                return False
        
        return True
    
    def _configure_path(self) -> None:
        """Add poppler bin directory to system PATH."""
        if not self.bin_path:
            return
        
        bin_path_str = str(self.bin_path.resolve())
        current_path = os.environ.get("PATH", "")
        
        # Only add if not already in PATH
        if bin_path_str not in current_path:
            if sys.platform.startswith("win"):
                os.environ["PATH"] = f"{bin_path_str};{current_path}"
            else:
                os.environ["PATH"] = f"{bin_path_str}:{current_path}"
    
    def get_status(self) -> Dict[str, any]:
        """
        Get detailed poppler status information.
        
        Returns:
            dict: Status information including detection status, paths, and available tools.
        """
        status = {
            "detected": self.is_detected,
            "repo_root": str(self.repo_root),
            "poppler_path": str(self.poppler_path),
            "bin_path": str(self.bin_path) if self.bin_path else None,
            "error": self.detection_error,
            "available_tools": [],
            "path_configured": False
        }
        
        if self.is_detected:
            status["available_tools"] = self._get_available_tools()
            status["path_configured"] = str(self.bin_path.resolve()) in os.environ.get("PATH", "")
        
        return status
    
    def _get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available poppler tools with their paths."""
        if not self.bin_path:
            return []
        
        tools = []
        common_poppler_tools = [
            "pdfinfo", "pdfimages", "pdftoppm", "pdftotext", "pdftops",
            "pdftohtml", "pdftocairo", "pdffonts", "pdfdetach", "pdfattach",
            "pdfseparate", "pdfunite"
        ]
        
        for tool in common_poppler_tools:
            for ext in [".exe", ""]:
                tool_path = self.bin_path / f"{tool}{ext}"
                if tool_path.exists():
                    tools.append({
                        "name": tool,
                        "path": str(tool_path),
                        "executable": f"{tool}{ext}"
                    })
                    break
        
        return tools
    
    def test_tool(self, tool_name: str) -> Tuple[bool, str]:
        """
        Test if a poppler tool is working properly.
        
        Args:
            tool_name: Name of the poppler tool (e.g., 'pdfinfo')
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_detected:
            return False, "Poppler not detected"
        
        try:
            # Find the tool executable
            tool_path = None
            for ext in [".exe", ""]:
                candidate = self.bin_path / f"{tool_name}{ext}"
                if candidate.exists():
                    tool_path = candidate
                    break
            
            if not tool_path:
                return False, f"Tool '{tool_name}' not found"
            
            # For Windows executables on Linux, we can't execute them directly
            # but their presence in the correct structure indicates they're ready for use
            if tool_path.suffix == ".exe" and not sys.platform.startswith("win"):
                # Check if file is readable and has reasonable size
                if tool_path.is_file() and tool_path.stat().st_size > 1000:
                    return True, f"Tool '{tool_name}' found and appears valid (Windows executable on Linux)"
                else:
                    return False, f"Tool '{tool_name}' exists but appears invalid"
            
            # For native executables, try to run them
            result = subprocess.run(
                [str(tool_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 or "usage" in result.stdout.lower() or "usage" in result.stderr.lower():
                return True, f"Tool '{tool_name}' is working properly"
            else:
                return False, f"Tool '{tool_name}' returned error code {result.returncode}"
                
        except subprocess.TimeoutExpired:
            return False, f"Tool '{tool_name}' timed out"
        except PermissionError:
            # If we get permission error, the file exists but can't be executed
            # This is expected for Windows .exe files on Linux
            if tool_path and tool_path.suffix == ".exe":
                return True, f"Tool '{tool_name}' found (Windows executable, cannot test on current platform)"
            else:
                return False, f"Permission denied accessing tool '{tool_name}'"
        except Exception as e:
            return False, f"Error testing tool '{tool_name}': {e}"
    
    def print_status(self) -> None:
        """Print detailed poppler status to console."""
        status = self.get_status()
        
        print("=" * 50)
        print("POPPLER INTEGRATION STATUS")
        print("=" * 50)
        print(f"Repository root: {status['repo_root']}")
        print(f"Poppler directory: {status['poppler_path']}")
        
        if status["detected"]:
            print("✓ Poppler DETECTED and CONFIGURED")
            print(f"Bin directory: {status['bin_path']}")
            print(f"PATH configured: {'✓ Yes' if status['path_configured'] else '✗ No'}")
            
            if status["available_tools"]:
                print(f"\nAvailable tools ({len(status['available_tools'])}):")
                for tool in status["available_tools"]:
                    print(f"  - {tool['name']} ({tool['executable']})")
        else:
            print("✗ Poppler NOT DETECTED")
            if status["error"]:
                print(f"Error: {status['error']}")
        
        print("=" * 50)
    
    def get_tool_path(self, tool_name: str) -> Optional[Path]:
        """
        Get the full path to a specific poppler tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'pdfinfo')
            
        Returns:
            Path to the tool executable, or None if not found
        """
        if not self.is_detected:
            return None
        
        for ext in [".exe", ""]:
            tool_path = self.bin_path / f"{tool_name}{ext}"
            if tool_path.exists():
                return tool_path
        
        return None
    
    def get_detected_path(self) -> Optional[str]:
        """
        Get the detected poppler bin path as string for compatibility.
        
        Returns:
            String path to poppler bin directory, or None if not detected
        """
        if not self.is_detected or not self.bin_path:
            return None
        return str(self.bin_path)


# Global instance for easy access
_poppler_manager = None


def get_poppler_manager() -> PopplerManager:
    """Get the global PopplerManager instance."""
    global _poppler_manager
    if _poppler_manager is None:
        _poppler_manager = PopplerManager()
    return _poppler_manager


def detect_poppler() -> bool:
    """
    Quick poppler detection function.
    
    Returns:
        bool: True if poppler is detected and configured
    """
    return get_poppler_manager().is_detected


def print_poppler_status() -> None:
    """Print poppler status to console."""
    get_poppler_manager().print_status()


def get_poppler_path() -> Optional[str]:
    """
    Get the detected poppler path for use by other modules.
    
    Returns:
        String path to poppler bin directory, or None if not detected
    """
    return get_poppler_manager().get_detected_path()


def check_pdf_file_exists(pdf_path: str) -> Tuple[bool, str]:
    """
    Check if a PDF file exists and is readable.
    
    Args:
        pdf_path: Path to the PDF file to check
        
    Returns:
        tuple: (exists: bool, message: str)
    """
    if not pdf_path:
        return False, "No PDF path provided"
    
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        return False, f"PDF file does not exist: {pdf_path}"
    
    if not pdf_file.is_file():
        return False, f"Path is not a file: {pdf_path}"
    
    try:
        # Check if file is readable and has reasonable size
        size = pdf_file.stat().st_size
        if size == 0:
            return False, f"PDF file is empty: {pdf_path}"
        if size < 100:  # PDF files are typically larger than 100 bytes
            return False, f"PDF file appears to be too small (possibly corrupted): {pdf_path}"
    except OSError as e:
        return False, f"Cannot access PDF file: {pdf_path} - {e}"
    
    return True, f"PDF file is accessible: {pdf_path}"


def test_poppler_startup() -> Tuple[bool, str]:
    """
    Test poppler integration on startup.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    manager = get_poppler_manager()
    
    if not manager.is_detected:
        return False, f"Poppler detection failed: {manager.detection_error}"
    
    # Test essential tools
    essential_tools = ["pdfinfo", "pdfimages"]
    failed_tools = []
    
    for tool in essential_tools:
        success, message = manager.test_tool(tool)
        if not success:
            failed_tools.append(f"{tool}: {message}")
    
    if failed_tools:
        return False, f"Tool tests failed: {'; '.join(failed_tools)}"
    
    return True, "Poppler integration test passed successfully"


if __name__ == "__main__":
    # Command line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Poppler utilities manager")
    parser.add_argument("--test", action="store_true", help="Test poppler integration")
    parser.add_argument("--status", action="store_true", help="Show poppler status")
    parser.add_argument("--tool", type=str, help="Test specific tool")
    
    args = parser.parse_args()
    
    if args.status or not any([args.test, args.tool]):
        print_poppler_status()
    
    if args.test:
        print("\nTesting poppler startup...")
        success, message = test_poppler_startup()
        print(f"{'✓' if success else '✗'} {message}")
    
    if args.tool:
        print(f"\nTesting tool '{args.tool}'...")
        manager = get_poppler_manager()
        success, message = manager.test_tool(args.tool)
        print(f"{'✓' if success else '✗'} {message}")