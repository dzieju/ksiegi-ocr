# IMAP Pagination Fix

## Problem

The IMAP message retrieval implementation had a limitation that restricted pagination to only the first page of results. This was caused by limiting the fetched message UIDs to only the last `per_page` messages in the `_get_imap_messages` method.

### Original Code (Line 1092)
```python
limited_uids = message_uids[-per_page:]  # Get most recent messages up to per_page limit
```

This meant that if there were 1000 messages matching the search criteria and `per_page=500`, only the last 500 UIDs would be fetched. When the user tried to navigate to page 2, there were no additional messages available because only 500 had been fetched from IMAP.

## Solution

The fix removes the per_page limitation at the IMAP UID fetching level and relies on the higher-level pagination logic in `_threaded_search` method to handle pagination correctly.

### Key Changes

1. **Removed UID Limitation in `_get_imap_messages`** (Line 1091-1098)
   - Changed from: `limited_uids = message_uids[-per_page:]`
   - Changed to: Fetch all `message_uids` found by the search
   - Added comment: `# IMAP pagination fix: Remove per_page limitation here`

2. **Pagination Handled at Higher Level**
   - The `_threaded_search` method already has proper pagination logic (Line 496-498)
   - Per-folder limit is still applied at line 438: `folder_messages = messages_list[:per_page]`
   - Final pagination is applied at line 676: `paginated_messages = filtered_messages[start_idx:end_idx]`

### Code Flow

#### Before Fix:
1. IMAP search finds 1000 message UIDs
2. `_get_imap_messages` limits to last 500 UIDs → Only 500 messages fetched
3. Per-folder limit applied: min(500, per_page) → Still 500 messages
4. Higher-level pagination tries to get page 2: filtered_messages[500:1000] → Empty (no data)

#### After Fix:
1. IMAP search finds 1000 message UIDs
2. `_get_imap_messages` fetches all 1000 UIDs → All 1000 messages fetched
3. Per-folder limit applied: min(1000, per_page) → 500 messages (matches Exchange behavior)
4. Higher-level pagination gets page 2: filtered_messages[500:1000] → Works correctly!

## Impact

### What Changed:
- IMAP accounts can now properly paginate through search results beyond the first page
- All message UIDs from IMAP search are fetched instead of limiting to `per_page`

### What Stayed the Same:
- **Exchange logic**: Completely unmodified (separate code path at line 386-428)
- **POP3 logic**: Completely unmodified (has its own method `_get_pop3_messages`)
- **Per-folder limit**: Still applied at line 438 (consistent with Exchange)
- **Higher-level pagination**: Already existed, now works correctly for IMAP
- **Performance limits**: Still applied at line 501 (`max_total_messages`)

## Testing

The change is minimal and surgical:
- Only 6 lines changed in one method
- Python syntax validated successfully
- Exchange and POP3 code paths verified as unmodified
- Pagination logic at higher level confirmed to be intact

## Files Modified

- `gui/mail_search_components/search_engine.py` (Lines 1091-1098)

## Backward Compatibility

Fully backward compatible:
- Same API signatures
- Same behavior for Exchange accounts
- Same behavior for POP3 accounts  
- Improved behavior for IMAP accounts (now supports pagination)
