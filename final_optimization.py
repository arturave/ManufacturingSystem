#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final optimization - remove all remaining debug statements and optimize performance
"""

import re
from pathlib import Path

def final_cleanup(file_path):
    """Final cleanup of debug statements"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned_lines = []
    skip_next = False
    in_debug_block = False

    for i, line in enumerate(lines):
        # Skip empty print statements
        if 'print(' in line and ('DEBUG' in line or 'debug' in line.lower() or
                                '="*50' in line or '="*60' in line or 'NOT FOUND' in line):
            continue

        # Skip debug log writing
        if 'product_update_debug.log' in line:
            continue

        # Skip debug comments
        if '# DEBUG:' in line or '# Debug' in line:
            continue

        # Skip lines that are part of debug blocks
        if 'debug_log' in line:
            continue

        # Keep the line
        cleaned_lines.append(line)

    return ''.join(cleaned_lines)

def optimize_files():
    """Final optimization pass"""
    base_dir = Path(__file__).parent

    files = [
        'products_module_enhanced.py',
        'part_edit_enhanced_v4.py'
    ]

    for file_name in files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"Final optimization of {file_name}...")

            # Read and clean
            content = final_cleanup(file_path)

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  Optimized {file_name}")

if __name__ == "__main__":
    optimize_files()