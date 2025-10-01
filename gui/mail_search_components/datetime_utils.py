"""
Datetime utilities for IMAP client date handling.
This module provides robust datetime methods to replace any potential split() operations.
"""
import email.utils
from datetime import datetime, timezone, timedelta
from tools.logger import log


class IMAPDateHandler:
    """
    Handles all datetime operations for IMAP client with proper methods.
    Explicitly avoids any .split() operations on datetime objects.
    """
    
    @staticmethod
    def parse_imap_date(date_string):
        """
        Parse IMAP date string to datetime object using proper datetime methods.
        
        Args:
            date_string: Date string from IMAP envelope or datetime object
            
        Returns:
            datetime: Parsed datetime object with timezone
        """
        try:
            if not date_string:
                return datetime.now(timezone.utc)
            
            # Check if input is already a datetime object - don't re-parse
            if isinstance(date_string, datetime):
                # Ensure timezone is set
                if date_string.tzinfo is None:
                    return date_string.replace(tzinfo=timezone.utc)
                return date_string
            
            # Handle bytes to string conversion
            if isinstance(date_string, bytes):
                date_string = date_string.decode('utf-8', errors='ignore')
            
            # Use email.utils.parsedate_to_datetime for proper parsing
            parsed_date = email.utils.parsedate_to_datetime(str(date_string))
            
            # Ensure timezone is set
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            
            return parsed_date
            
        except Exception as e:
            log(f"[DATETIME] Error parsing IMAP date '{date_string}': {str(e)}")
            return datetime.now(timezone.utc)
    
    @staticmethod
    def format_display_date(dt):
        """
        Format datetime for display using proper strftime method.
        
        Args:
            dt: datetime object
            
        Returns:
            str: Formatted date string (YYYY-MM-DD HH:MM)
        """
        if not dt:
            return 'Brak daty'
        
        try:
            # Use strftime for proper formatting - never split()
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            log(f"[DATETIME] Error formatting display date: {str(e)}")
            return 'Błąd daty'
    
    @staticmethod
    def format_imap_search_date(dt):
        """
        Format datetime for IMAP search criteria using proper strftime method.
        
        Args:
            dt: datetime object
            
        Returns:
            str: IMAP-compatible date string (DD-MMM-YYYY)
        """
        if not dt:
            return None
        
        try:
            # Use strftime for IMAP search format - never split()
            return dt.strftime("%d-%b-%Y")
        except Exception as e:
            log(f"[DATETIME] Error formatting IMAP search date: {str(e)}")
            return None
    
    @staticmethod
    def format_monthly_folder(dt):
        """
        Format datetime for monthly folder naming using proper strftime method.
        
        Args:
            dt: datetime object
            
        Returns:
            str: Monthly folder name (MM.YYYY)
        """
        if not dt:
            dt = datetime.now()
        
        try:
            # Use strftime for folder naming - never split()
            return dt.strftime("%m.%Y")
        except Exception as e:
            log(f"[DATETIME] Error formatting monthly folder: {str(e)}")
            return datetime.now().strftime("%m.%Y")
    
    @staticmethod
    def format_email_header_date(dt):
        """
        Format datetime for email headers using proper email.utils method.
        
        Args:
            dt: datetime object
            
        Returns:
            str: RFC-compliant email date string
        """
        if not dt:
            dt = datetime.now(timezone.utc)
        
        try:
            # Use email.utils.formatdate for proper RFC formatting - never split()
            return email.utils.formatdate(dt.timestamp(), localtime=True)
        except Exception as e:
            log(f"[DATETIME] Error formatting email header date: {str(e)}")
            return email.utils.formatdate(localtime=True)
    
    @staticmethod
    def get_period_start_date(period_name):
        """
        Calculate start date for a named period using proper datetime arithmetic.
        
        Args:
            period_name: Name of the period (e.g., "ostatni_tydzien")
            
        Returns:
            datetime: Start date for the period
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Use timedelta for date calculations - never split()
            if period_name == "ostatni_tydzien":
                return now - timedelta(days=7)
            elif period_name == "ostatnie_2_tygodnie":
                return now - timedelta(days=14)
            elif period_name == "ostatni_miesiac":
                return now - timedelta(days=30)
            elif period_name == "ostatnie_3_miesiace":
                return now - timedelta(days=90)
            elif period_name == "ostatnie_6_miesiecy":
                return now - timedelta(days=180)
            elif period_name == "ostatni_rok":
                return now - timedelta(days=365)
            else:
                return None
                
        except Exception as e:
            log(f"[DATETIME] Error calculating period start date: {str(e)}")
            return None
    
    @staticmethod
    def get_date_range(period_name):
        """
        Get date range (start_date, end_date) for a named period.
        
        Args:
            period_name: Name of the period (e.g., "ostatni_tydzien", "wszystkie")
            
        Returns:
            tuple: (start_date, end_date) datetime tuple, or None for "wszystkie"
        """
        try:
            # "wszystkie" means no date filtering
            if period_name == "wszystkie" or not period_name:
                return None
            
            # Get start date for the period
            start_date = IMAPDateHandler.get_period_start_date(period_name)
            if start_date is None:
                return None
            
            # End date is current date/time
            end_date = datetime.now(timezone.utc)
            
            return (start_date, end_date)
            
        except Exception as e:
            log(f"[DATETIME] Error calculating date range: {str(e)}")
            return None
    
    @staticmethod
    def convert_to_timestamp(dt):
        """
        Convert datetime to timestamp using proper datetime methods.
        
        Args:
            dt: datetime object
            
        Returns:
            float: Unix timestamp
        """
        if not dt:
            return None
        
        try:
            # Use .timestamp() method - never split()
            return dt.timestamp()
        except Exception as e:
            log(f"[DATETIME] Error converting to timestamp: {str(e)}")
            return None
    
    @staticmethod
    def ensure_timezone(dt, default_tz=timezone.utc):
        """
        Ensure datetime object has timezone information using proper methods.
        
        Args:
            dt: datetime object
            default_tz: Default timezone if none present
            
        Returns:
            datetime: Datetime with timezone
        """
        if not dt:
            return datetime.now(default_tz)
        
        try:
            if dt.tzinfo is None:
                # Use .replace() method to add timezone - never split()
                return dt.replace(tzinfo=default_tz)
            return dt
        except Exception as e:
            log(f"[DATETIME] Error ensuring timezone: {str(e)}")
            return datetime.now(default_tz)
    
    @staticmethod
    def safe_datetime_comparison(dt1, dt2):
        """
        Safely compare two datetime objects using proper methods.
        
        Args:
            dt1: First datetime object
            dt2: Second datetime object
            
        Returns:
            int: -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2
        """
        try:
            # Ensure both have timezones
            dt1 = IMAPDateHandler.ensure_timezone(dt1)
            dt2 = IMAPDateHandler.ensure_timezone(dt2)
            
            # Use proper comparison operators - never split()
            if dt1 < dt2:
                return -1
            elif dt1 > dt2:
                return 1
            else:
                return 0
                
        except Exception as e:
            log(f"[DATETIME] Error comparing datetimes: {str(e)}")
            return 0
    
    @staticmethod
    def validate_datetime_object(dt):
        """
        Validate that an object is a proper datetime and not a string that needs splitting.
        
        Args:
            dt: Object to validate
            
        Returns:
            bool: True if valid datetime object
        """
        try:
            if isinstance(dt, datetime):
                # Ensure it has proper methods and is not corrupted
                # Test basic datetime operations without split()
                _ = dt.strftime('%Y')
                _ = dt.year
                _ = dt.month 
                _ = dt.day
                return True
            return False
        except Exception as e:
            log(f"[DATETIME] Invalid datetime object: {str(e)}")
            return False