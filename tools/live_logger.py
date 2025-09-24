#!/usr/bin/env python3
"""
Live logging system that captures stdout/stderr in real-time.

This module provides a way to capture and display live logs from the current
session without loading historical log files.
"""

import sys
import io
import threading
from collections import deque
from typing import List, Optional, Callable


class LiveLogCapture:
    """Captures stdout/stderr in real-time and maintains a circular buffer."""
    
    def __init__(self, max_lines: int = 1000):
        """
        Initialize the live log capture.
        
        Args:
            max_lines: Maximum number of lines to keep in memory
        """
        self.max_lines = max_lines
        self.log_buffer = deque(maxlen=max_lines)
        self.observers = []  # Callbacks to notify when new logs arrive
        self.lock = threading.Lock()
        
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Create wrapper streams
        self.stdout_wrapper = LoggingWrapper(self.original_stdout, self._add_log_line, "STDOUT")
        self.stderr_wrapper = LoggingWrapper(self.original_stderr, self._add_log_line, "STDERR")
        
        self.is_capturing = False
    
    def start_capture(self):
        """Start capturing stdout/stderr."""
        if not self.is_capturing:
            sys.stdout = self.stdout_wrapper
            sys.stderr = self.stderr_wrapper
            self.is_capturing = True
            self._add_log_line("=== Live log capture started ===", "SYSTEM")
    
    def stop_capture(self):
        """Stop capturing stdout/stderr."""
        if self.is_capturing:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            self.is_capturing = False
            self._add_log_line("=== Live log capture stopped ===", "SYSTEM")
    
    def _add_log_line(self, line: str, source: str = "STDOUT"):
        """Add a log line to the buffer."""
        with self.lock:
            # Add timestamp and source prefix
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_line = f"[{timestamp}] {source}: {line.rstrip()}"
            self.log_buffer.append(formatted_line)
            
            # Notify observers
            for callback in self.observers:
                try:
                    callback(formatted_line)
                except Exception as e:
                    # Don't let observer errors break logging
                    print(f"Observer error: {e}", file=self.original_stderr)
    
    def get_logs(self) -> List[str]:
        """Get all current logs as a list."""
        with self.lock:
            return list(self.log_buffer)
    
    def get_logs_text(self) -> str:
        """Get all current logs as a single string."""
        return "\n".join(self.get_logs())
    
    def clear_logs(self):
        """Clear the log buffer."""
        with self.lock:
            self.log_buffer.clear()
            self._add_log_line("=== Log buffer cleared ===", "SYSTEM")
    
    def add_observer(self, callback: Callable[[str], None]):
        """Add a callback to be notified of new log lines."""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[str], None]):
        """Remove a log observer."""
        if callback in self.observers:
            self.observers.remove(callback)


class LoggingWrapper:
    """Wrapper for stdout/stderr that captures output while preserving original functionality."""
    
    def __init__(self, original_stream, log_callback: Callable[[str, str], None], source: str):
        """
        Initialize the wrapper.
        
        Args:
            original_stream: The original stdout/stderr stream
            log_callback: Callback to receive log lines
            source: Source identifier (STDOUT/STDERR)
        """
        self.original_stream = original_stream
        self.log_callback = log_callback
        self.source = source
    
    def write(self, text: str):
        """Write text to both original stream and log capture."""
        # Write to original stream first
        if hasattr(self.original_stream, 'write'):
            self.original_stream.write(text)
        
        # Capture for logging (split by lines)
        if text.strip():  # Only log non-empty content
            lines = text.split('\n')
            for line in lines:
                if line.strip():  # Skip empty lines
                    self.log_callback(line, self.source)
    
    def flush(self):
        """Flush the original stream."""
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()
    
    def __getattr__(self, name):
        """Delegate all other attributes to the original stream."""
        return getattr(self.original_stream, name)


# Global instance for easy access
_global_capture = None


def get_live_logger() -> LiveLogCapture:
    """Get the global live logger instance."""
    global _global_capture
    if _global_capture is None:
        _global_capture = LiveLogCapture()
    return _global_capture


def start_live_logging():
    """Start live logging capture."""
    get_live_logger().start_capture()


def stop_live_logging():
    """Stop live logging capture."""
    get_live_logger().stop_capture()


def get_current_logs() -> str:
    """Get current session logs as text."""
    return get_live_logger().get_logs_text()


def clear_current_logs():
    """Clear current session logs."""
    get_live_logger().clear_logs()


if __name__ == "__main__":
    # Test the live logger
    logger = LiveLogCapture()
    logger.start_capture()
    
    print("This is a test message to stdout")
    print("This is stderr message", file=sys.stderr)
    
    import time
    time.sleep(0.1)  # Give time for capture
    
    print("Current logs:")
    print(logger.get_logs_text())
    
    logger.stop_capture()