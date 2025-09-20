# Layout Fix for Wyniki/Logi Section

## Problem
The "Wyniki/Logi" (Results/Logs) section in the Księgi tab was not expanding to fill available vertical space, leaving empty space at the bottom of the window when resized.

## Root Cause
The issue was in the `sticky` parameter configuration in `gui/tab_ksiegi.py`:

**Before (problematic):**
```python
results_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
results_inner.grid(row=0, column=0, sticky="ew", padx=0, pady=0)  
self.text_area.grid(row=0, column=0, sticky="ew", pady=0, padx=0)
```

The containers were using `sticky="ew"` (east-west only) instead of `sticky="nsew"` (north-south-east-west), preventing vertical expansion.

## Solution
**After (fixed):**
```python
results_frame.grid(row=current_row, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
results_inner.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
self.text_area.grid(row=0, column=0, sticky="nsew", pady=0, padx=0)
```

## Changes Made
1. **Fixed sticky parameters**: Changed from `"ew"` to `"nsew"` for:
   - `results_frame.grid()` 
   - `results_inner.grid()`
   - `self.text_area.grid()`

2. **Removed redundant code**: Eliminated duplicate `grid_configure()` calls that were trying to fix the same issue:
   - Removed `results_frame.grid_configure(sticky="nsew")`  
   - Removed `results_inner.grid_configure(sticky="nsew")`
   - Removed `self.text_area.grid_configure(sticky="nsew")`

3. **Kept essential weight configuration**: Maintained the critical weight settings:
   - `scroll_frame.grid_rowconfigure(current_row, weight=1)` 
   - `results_inner.grid_rowconfigure(0, weight=1)`

## Expected Behavior After Fix
- ✅ Wyniki/Logi section expands to fill all available vertical space
- ✅ Section resizes dynamically when window is resized  
- ✅ No empty space at the bottom of the tab
- ✅ Text area scrolls properly when content overflows
- ✅ Horizontal expansion still works as before

## Files Modified
- `gui/tab_ksiegi.py` (lines 133, 137, 141, and cleanup of lines 152-154)

## Testing
To test the fix:
1. Run the application: `python main.py`
2. Navigate to the "Księgi" tab
3. Resize the window vertically and horizontally
4. Verify that the Wyniki/Logi section expands/contracts to fill available space
5. Check that there's no empty space at the bottom of the section