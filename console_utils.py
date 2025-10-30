#!/usr/bin/env python3
"""
Console Utilities for Cross-Platform Compatibility

Provides utilities for handling console output on both Unix-like systems and Windows,
specifically addressing Unicode character encoding issues on Windows consoles.
"""

import sys
import os


def setup_console_encoding():
    """
    Setup console encoding to support UTF-8 on Windows.

    This function attempts to configure the console to use UTF-8 encoding,
    which allows printing Unicode characters like ✓ and ✗.

    On Windows, this sets the console code page to UTF-8 (65001).
    On Unix-like systems, this is typically not needed as UTF-8 is the default.
    """
    if sys.platform.startswith('win'):
        try:
            # Try to set console to UTF-8
            os.system('chcp 65001 >nul 2>&1')

            # Reconfigure stdout and stderr to use UTF-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # If setup fails, safe_print will fall back to ASCII
            pass


def safe_print(text, use_unicode=True, file=None):
    """
    Print text safely, handling Unicode encoding errors on Windows.

    Args:
        text: The text to print
        use_unicode: Whether to attempt using Unicode characters (default: True)
        file: Optional file object to write to (default: sys.stdout)

    This function will:
    1. First try to print with Unicode characters
    2. If that fails, replace Unicode symbols with ASCII equivalents
    3. Always succeeds without raising encoding errors
    """
    if file is None:
        file = sys.stdout

    try:
        # Try to print with Unicode
        print(text, file=file)
    except UnicodeEncodeError:
        # Fall back to ASCII-compatible version
        ascii_text = text.replace('✓', '[OK]').replace('✗', '[X]')

        # Additional common Unicode replacements
        replacements = {
            '→': '->',
            '←': '<-',
            '↓': '|',
            '↑': '^',
            '•': '*',
            '–': '-',
            '—': '--',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '…': '...',
        }

        for unicode_char, ascii_char in replacements.items():
            ascii_text = ascii_text.replace(unicode_char, ascii_char)

        try:
            print(ascii_text, file=file)
        except Exception as e:
            # Last resort: print as ASCII with errors replaced
            safe_text = ascii_text.encode('ascii', errors='replace').decode('ascii')
            print(safe_text, file=file)


def get_check_symbol():
    """
    Get the appropriate check/success symbol for the current platform.

    Returns:
        '✓' on systems with UTF-8 support, '[OK]' on Windows with limited encoding
    """
    if sys.platform.startswith('win'):
        # Try to detect if we can use Unicode
        try:
            sys.stdout.buffer.write('✓'.encode(sys.stdout.encoding or 'utf-8'))
            sys.stdout.buffer.flush()
            return '✓'
        except (UnicodeEncodeError, AttributeError, LookupError):
            return '[OK]'
    return '✓'


def get_cross_symbol():
    """
    Get the appropriate cross/error symbol for the current platform.

    Returns:
        '✗' on systems with UTF-8 support, '[X]' on Windows with limited encoding
    """
    if sys.platform.startswith('win'):
        # Try to detect if we can use Unicode
        try:
            sys.stdout.buffer.write('✗'.encode(sys.stdout.encoding or 'utf-8'))
            sys.stdout.buffer.flush()
            return '✗'
        except (UnicodeEncodeError, AttributeError, LookupError):
            return '[X]'
    return '✗'


# Initialize console encoding when module is imported
setup_console_encoding()


# Export commonly used symbols
CHECK = get_check_symbol()
CROSS = get_cross_symbol()
