#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix all remaining syntax errors in products_module_enhanced.py
"""

import re
from pathlib import Path

def fix_syntax_errors():
    """Fix all syntax errors in products_module_enhanced.py"""

    file_path = Path("products_module_enhanced.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip orphaned f.write statements
        if 'f.write(' in line and 'with open' not in lines[max(0, i-5):i]:
            i += 1
            continue

        # Fix empty if/else blocks
        if line.strip().startswith('if ') and line.strip().endswith(':'):
            # Check if next non-empty line is else or elif
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (lines[j].strip().startswith('else:') or
                                  lines[j].strip().startswith('elif ')):
                # Empty if block - add pass
                fixed_lines.append(line)
                fixed_lines.append(' ' * (len(line) - len(line.lstrip()) + 4) + 'pass\n')
                i += 1
                continue

        # Fix empty else blocks
        if line.strip() == 'else:':
            # Check if next non-empty line is at wrong indentation
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j]
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                # If next line is at same or lower indentation, else block is empty
                if next_indent <= current_indent:
                    # Skip the empty else block
                    i += 1
                    continue

        # Fix empty except blocks
        if line.strip().startswith('except ') and line.strip().endswith(':'):
            # Check if next non-empty line is at wrong indentation
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j]
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                # If next line is at same or lower indentation, except block is empty
                if next_indent <= current_indent:
                    fixed_lines.append(line)
                    fixed_lines.append(' ' * (current_indent + 4) + 'pass\n')
                    i += 1
                    continue

        # Fix wrong indentation for hasattr line
        if 'if hasattr(update_error,' in line:
            # Ensure correct indentation (should be inside except block)
            line = '                        ' + line.lstrip()

        fixed_lines.append(line)
        i += 1

    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    print(f"Fixed syntax errors in {file_path}")

if __name__ == "__main__":
    fix_syntax_errors()