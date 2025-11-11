#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the enhanced products module
Tests new functionality and database integration
"""

import sys
import os
import customtkinter as ctk
from tkinter import messagebox

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to test
from database import Database
from products_module_enhanced import EnhancedProductsWindow
from part_edit_enhanced_v4 import EnhancedPartEditDialogV4

def test_products_module():
    """Test the enhanced products module"""
    print("Testing Enhanced Products Module...")

    # Initialize database
    try:
        db = Database()
        print("✓ Database connected")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

    # Create test application
    root = ctk.CTk()
    root.title("Test Products Module")
    root.geometry("400x300")

    # Test counter
    test_results = []

    def test_products_window():
        """Open products window"""
        try:
            window = EnhancedProductsWindow(root, db)
            print("✓ Products window opened successfully")
            test_results.append(True)

            # Check if filters are working
            if hasattr(window, 'search_entry'):
                print("✓ Search field available")
                test_results.append(True)
            else:
                print("✗ Search field not found")
                test_results.append(False)

            # Check if table is displayed
            if hasattr(window, 'products_container'):
                print("✓ Products container available")
                test_results.append(True)
            else:
                print("✗ Products container not found")
                test_results.append(False)

        except Exception as e:
            print(f"✗ Failed to open products window: {e}")
            test_results.append(False)

    def test_add_product_dialog():
        """Test add product dialog"""
        try:
            dialog = EnhancedPartEditDialogV4(
                root,
                db,
                [],
                catalog_mode=True,
                title="Test Add Product"
            )
            print("✓ Add product dialog opened")
            test_results.append(True)

            # Check for new features
            if hasattr(dialog, 'additional_doc_binary'):
                print("✓ Documentation field available")
                test_results.append(True)
            else:
                print("✗ Documentation field not found")
                test_results.append(False)

            if hasattr(dialog, 'catalog_mode'):
                print(f"✓ Catalog mode: {dialog.catalog_mode}")
                test_results.append(True)
            else:
                print("✗ Catalog mode not set")
                test_results.append(False)

            dialog.destroy()

        except Exception as e:
            print(f"✗ Failed to open add product dialog: {e}")
            test_results.append(False)

    def test_view_only_mode():
        """Test view-only mode"""
        try:
            # Create dummy product data
            dummy_product = {
                'id': 'test-123',
                'name': 'Test Product',
                'material_id': None,
                'thickness_mm': 2.0,
                'idx_code': 'TEST-001'
            }

            dialog = EnhancedPartEditDialogV4(
                root,
                db,
                [],
                part_data=dummy_product,
                view_only=True,
                title="Test View Product"
            )
            print("✓ View-only dialog opened")
            test_results.append(True)

            # Check if fields are disabled
            if dialog.name_entry.cget('state') == 'disabled':
                print("✓ Fields are disabled in view-only mode")
                test_results.append(True)
            else:
                print("✗ Fields not disabled in view-only mode")
                test_results.append(False)

            dialog.destroy()

        except Exception as e:
            print(f"✗ Failed to test view-only mode: {e}")
            test_results.append(False)

    # Create test UI
    ctk.CTkLabel(root, text="Products Module Test Suite",
                 font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

    ctk.CTkButton(
        root,
        text="Test Products Window",
        command=test_products_window,
        width=200
    ).pack(pady=10)

    ctk.CTkButton(
        root,
        text="Test Add Product Dialog",
        command=test_add_product_dialog,
        width=200
    ).pack(pady=10)

    ctk.CTkButton(
        root,
        text="Test View-Only Mode",
        command=test_view_only_mode,
        width=200
    ).pack(pady=10)

    def show_results():
        """Show test results"""
        passed = sum(test_results)
        total = len(test_results)

        print("\n" + "="*40)
        print(f"Test Results: {passed}/{total} passed")
        print("="*40)

        if passed == total:
            messagebox.showinfo("Test Results",
                              f"All tests passed! ({passed}/{total})")
        else:
            messagebox.showwarning("Test Results",
                                 f"Some tests failed: {passed}/{total} passed")

        root.quit()

    ctk.CTkButton(
        root,
        text="Show Results & Exit",
        command=show_results,
        width=200,
        fg_color="#4CAF50"
    ).pack(pady=20)

    # Run the application
    root.mainloop()

    return all(test_results) if test_results else False

if __name__ == "__main__":
    print("Starting Products Module Tests...")
    print("="*40)

    success = test_products_module()

    if success:
        print("\n✓ All tests passed successfully!")
    else:
        print("\n✗ Some tests failed. Check the output above.")

    input("\nPress Enter to exit...")