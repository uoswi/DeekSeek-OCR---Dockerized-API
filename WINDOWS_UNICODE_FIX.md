# Windows Unicode Encoding Fix

## Problem

When running Python scripts on Windows that use Unicode characters (like ✓ and ✗), you may encounter:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 0: character maps to <undefined>
```

This happens because Windows console uses cp1252 encoding by default instead of UTF-8.

## Solution

### Option 1: Use the console_utils Module (Recommended)

We've created a `console_utils.py` module that handles Windows compatibility automatically.

**Download the module:**
- Copy `console_utils.py` from this repository to your project directory

**Update your script:**

```python
# At the top of your script, add:
try:
    from console_utils import safe_print, CHECK, CROSS
except ImportError:
    # Fallback if console_utils is not available
    safe_print = print
    CHECK = '[OK]'
    CROSS = '[X]'

# Then replace print statements with Unicode characters:
# OLD:
print(f"✓ Saved cleaned markdown: {clean_filepath}")
print(f"\n✗ Error: {e}")

# NEW:
safe_print(f"{CHECK} Saved cleaned markdown: {clean_filepath}")
safe_print(f"\n{CROSS} Error: {e}")
```

### Option 2: Force UTF-8 Encoding at Script Start

Add this code at the very beginning of your script (before any print statements):

```python
import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform.startswith('win'):
    # Set environment variable
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # Reconfigure stdout and stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

### Option 3: Replace Unicode Characters with ASCII

If you prefer not to use the module, simply replace Unicode characters:

```python
# OLD:
print(f"✓ Success")
print(f"✗ Error")

# NEW:
print(f"[OK] Success")
print(f"[X] Error")
```

### Option 4: Set Console Code Page (Terminal Command)

Run this command in your terminal before running the script:

```cmd
chcp 65001
```

Or set it permanently in Windows:
1. Right-click on Command Prompt title bar
2. Select "Properties"
3. Under "Options" tab, check "Use Unicode UTF-8 for worldwide language support"

### Option 5: Run with PYTHONIOENCODING Environment Variable

```cmd
set PYTHONIOENCODING=utf-8
python your_script.py
```

Or in PowerShell:

```powershell
$env:PYTHONIOENCODING='utf-8'
python your_script.py
```

## Testing

After applying the fix, test with this simple script:

```python
from console_utils import safe_print, CHECK, CROSS

safe_print(f"{CHECK} This should work!")
safe_print(f"{CROSS} This should also work!")
print("Regular print still works!")
```

## Repository Changes

The following files have been updated to support Windows:
- `console_utils.py` - New module for cross-platform console output
- `runpod_handler.py` - Updated to use `safe_print`
- `upload_large_pdf_to_runpod.py` - Updated to use `safe_print`

## Additional Notes

- The `console_utils.py` module automatically detects the platform and chooses the best approach
- It provides fallback ASCII characters if UTF-8 encoding is not available
- All existing code remains compatible while gaining Windows support
- The module is fully self-contained and has no external dependencies

## Common Unicode Character Replacements

If you need to replace other Unicode characters:

| Unicode | Codepoint | ASCII Alternative |
|---------|-----------|-------------------|
| ✓       | U+2713    | [OK] or [+]       |
| ✗       | U+2717    | [X] or [-]        |
| →       | U+2192    | ->                |
| ←       | U+2190    | <-                |
| •       | U+2022    | *                 |
| …       | U+2026    | ...               |
| –       | U+2013    | -                 |
| —       | U+2014    | --                |

## References

- [Python Issue 1602: Windows console doesn't display Unicode characters](https://bugs.python.org/issue1602)
- [PEP 528 -- Change Windows console encoding to UTF-8](https://www.python.org/dev/peps/pep-0528/)
- [Python documentation on sys.stdout.reconfigure()](https://docs.python.org/3/library/sys.html#sys.stdout)
