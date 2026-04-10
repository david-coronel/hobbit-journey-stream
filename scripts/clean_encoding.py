#!/usr/bin/env python3
"""
Clean encoding issues in JSON data files.
Replaces problematic Unicode characters with ASCII equivalents.
"""

import json
import sys
from pathlib import Path

# Characters to replace
REPLACEMENTS = {
    '™': '(TM)',
    '®': '(R)', 
    '©': '(C)',
    '—': '-',    # em dash
    '–': '-',    # en dash
    ''': "'",     # smart single quotes
    ''': "'",
    '"': '"',     # smart double quotes
    '"': '"',
    '…': '...',  # ellipsis
    '\xa0': ' ',  # non-breaking space
    '\u200b': '', # zero-width space
    '\ufeff': '', # BOM
}


def clean_string(s):
    """Clean a string by replacing problematic characters."""
    if not isinstance(s, str):
        return s
    for old, new in REPLACEMENTS.items():
        s = s.replace(old, new)
    return s


def clean_object(obj):
    """Recursively clean an object."""
    if isinstance(obj, dict):
        return {k: clean_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_object(item) for item in obj]
    elif isinstance(obj, str):
        return clean_string(obj)
    return obj


def clean_file(filepath):
    """Clean a single JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned = clean_object(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    
    print(f'  Cleaned: {filepath}')


def main():
    """Clean all JSON files in data directory."""
    # Get script directory and find data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    
    if not data_dir.exists():
        print('Error: data/ directory not found')
        sys.exit(1)
    
    print('Cleaning JSON files...')
    for json_file in data_dir.glob('*.json'):
        try:
            clean_file(json_file)
        except Exception as e:
            print(f'  Error with {json_file}: {e}')
    
    print('Done!')


if __name__ == '__main__':
    main()
