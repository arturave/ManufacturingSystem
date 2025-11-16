#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the Manufacturing System Application with Debug Output

This script starts the integrated manufacturing system with enhanced debug logging
to help diagnose any issues with file loading from Supabase Storage.
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*70)
print("MANUFACTURING SYSTEM - INTEGRATED VERSION 1.1")
print("="*70)
print("\nStarting application with debug logging enabled...")
print("\n[INSTRUCTIONS]:")
print("1. Click 'Zarządzanie produktami' to open the product catalog")
print("2. Select a product with files and click 'Edytuj' to edit it")
print("3. Check if files are loaded and displayed correctly")
print("\n[WHAT TO CHECK]:")
print("- Are CAD 2D/3D files shown with their names?")
print("- Can you click 'Podgląd' to view the files?")
print("- Are thumbnails displayed correctly?")
print("- Can you download files using 'Pobierz' buttons?")
print("\n[DEBUG OUTPUT]:")
print("The console will show detailed information about:")
print("- URL fields in product data")
print("- File download attempts from Supabase Storage")
print("- Thumbnail generation process")
print("- Any errors that occur")
print("\n" + "="*70 + "\n")

try:
    from mfg_integrated import IntegratedManufacturingSystem

    # Start the application
    app = IntegratedManufacturingSystem()
    app.mainloop()

except Exception as e:
    print(f"\n[ERROR] Failed to start application: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")