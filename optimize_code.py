#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to remove debug statements and optimize code
"""

import re
import os
from pathlib import Path

def remove_debug_prints(file_path):
    """Remove debug print statements from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove lines with DEBUG prints
    patterns = [
        r'^\s*print\([^\)]*DEBUG[^\)]*\).*$\n?',
        r'^\s*print\(f[^\)]*DEBUG[^\)]*\).*$\n?',
        r'^\s*debug_log\.append\([^\)]*\).*$\n?',
        r'^\s*# DEBUG:.*$\n?',
    ]

    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Remove empty debug blocks
    content = re.sub(r'^\s*# Write debug to file\n\s*import json\n\s*from datetime import datetime\n\s*debug_log = \[\]\n', '', content, flags=re.MULTILINE)

    # Remove debug log writing
    content = re.sub(r'with open\(["\']debug_.*?\.txt["\'],.*?\n.*?\n.*?\n', '', content, flags=re.MULTILINE | re.DOTALL)

    return content

def optimize_files():
    """Optimize all Python files in the project"""
    base_dir = Path(__file__).parent

    files_to_optimize = [
        'products_module_enhanced.py',
        'part_edit_enhanced_v4.py',
        'storage_utils.py',
        'integrated_viewer_v2.py'
    ]

    for file_name in files_to_optimize:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"Optimizing {file_name}...")

            # Read original
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()

            # Remove debug prints
            optimized = remove_debug_prints(file_path)

            # Count removed lines
            original_lines = len(original.splitlines())
            optimized_lines = len(optimized.splitlines())
            removed = original_lines - optimized_lines

            # Write optimized
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(optimized)

            print(f"  Removed {removed} debug lines from {file_name}")
        else:
            print(f"  File not found: {file_name}")

    print("\nOptimization complete!")

if __name__ == "__main__":
    optimize_files()