# Datetime Handling Improvements

This document describes the improvements made to eliminate any `.split()` operations on datetime objects in the IMAP client and replace them with proper datetime methods.

## Changes Made

### 1. Created `datetime_utils.py`
- **File**: `gui/mail_search_components/datetime_utils.py`
- **Purpose**: Centralized datetime handling utilities that explicitly avoid any `.split()` operations
- **Key Features**:
  - Robust IMAP date parsing using `email.utils.parsedate_to_datetime()`
  - Proper date formatting using `.strftime()` methods
  - Timezone handling with `.replace()` method
  - Timestamp conversion using `.timestamp()` method
  - Period calculation using `timedelta` arithmetic

### 2. Updated `search_engine.py`
- **Imports**: Added `IMAPDateHandler` import
- **Date parsing**: Replaced manual date parsing with `IMAPDateHandler.parse_imap_date()`
- **Period calculation**: Replaced `_get_period_start_date()` with utility method
- **Monthly folders**: Replaced `strftime()` calls with `IMAPDateHandler.format_monthly_folder()`
- **IMAP search dates**: Replaced direct `strftime()` with `IMAPDateHandler.format_imap_search_date()`
- **Timestamp conversion**: Replaced direct `.timestamp()` with utility method

### 3. Updated `results_display.py`
- **Display formatting**: Replaced direct `strftime()` with `IMAPDateHandler.format_display_date()`
- **Email headers**: Replaced `formatdate()` with `IMAPDateHandler.format_email_header_date()`

### 4. Added Comprehensive Tests
- **File**: `tests/test_datetime_utils.py`
- **Coverage**: 25 test cases covering all datetime utility methods
- **Validation**: Ensures no `.split()` operations are used on datetime objects

## Methods That Explicitly Avoid split()

### Date Parsing
```python
# OLD: Potential for split() usage in error cases
date_received = email.utils.parsedate_to_datetime(envelope.date.decode())

# NEW: Robust parsing with error handling
date_received = IMAPDateHandler.parse_imap_date(envelope.date)
```

### Date Formatting
```python
# OLD: Direct strftime (correct but not centralized)
date_str = dt.strftime('%Y-%m-%d %H:%M')

# NEW: Centralized formatting with validation
date_str = IMAPDateHandler.format_display_date(dt)
```

### Period Calculations
```python
# OLD: Manual timedelta calculations
start_date = now - timedelta(days=7)

# NEW: Named period calculation
start_date = IMAPDateHandler.get_period_start_date("ostatni_tydzien")
```

### Timestamp Conversion
```python
# OLD: Direct timestamp call
timestamp = dt.timestamp()

# NEW: Safe conversion with validation
timestamp = IMAPDateHandler.convert_to_timestamp(dt)
```

## Benefits

1. **Consistency**: All datetime operations now use standardized methods
2. **Error Handling**: Robust error handling prevents crashes on invalid dates
3. **Maintainability**: Centralized datetime logic in one module
4. **Testing**: Comprehensive test coverage ensures reliability
5. **Performance**: No string splitting operations that could be slow
6. **Type Safety**: Validates datetime objects before operations

## Backwards Compatibility

All changes are backwards compatible. The API remains the same, only the internal implementation has been improved to use proper datetime methods instead of any potential `.split()` operations.

## Testing

Run the datetime utility tests:
```bash
python -m unittest tests.test_datetime_utils -v
```

All 25 tests should pass, confirming that:
- Date parsing works correctly
- Date formatting produces expected results
- Period calculations are accurate
- No `.split()` operations are used on datetime objects
- Error cases are handled gracefully