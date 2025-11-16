#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for editing existing products with debug logging
"""

import sys
import os
from pathlib import Path

# Fix Windows paths
sys.path.insert(0, str(Path(__file__).parent))

# Run main application
from mfg_integrated import IntegratedManufacturingSystem
import customtkinter as ctk


def main():
    print("\n" + "="*70)
    print("STARTING APPLICATION WITH DEBUG LOGGING")
    print("="*70)
    print("\nInstructions:")
    print("1. Click 'Zarządzanie produktami' to open the product catalog")
    print("2. Select a product and click 'Edytuj' to edit it")
    print("3. Watch the console for debug output")
    print("\nThe console will show:")
    print("- What URL fields are present in the product data")
    print("- Whether files are being downloaded from Supabase Storage")
    print("- Any errors that occur during file loading")
    print("\n" + "="*70 + "\n")

    # Start application
    app = IntegratedManufacturingSystem()
    app.mainloop()


if __name__ == "__main__":
    main()