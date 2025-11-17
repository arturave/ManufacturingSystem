#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Enhanced Product Selector Dialog
"""

import sys
import customtkinter as ctk
from products_selector_dialog import ProductSelectorDialog
from supabase_client_v4 import SupabaseClient


def test_dialog():
    """Test the product selector dialog"""
    # Initialize CTk
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Create root window
    root = ctk.CTk()
    root.title("Test Product Selector")
    root.geometry("400x200")

    # Initialize database
    db = SupabaseClient()

    def open_selector():
        """Open the product selector dialog"""
        def on_products_selected(products):
            print(f"\n=== SELECTED PRODUCTS ===")
            for i, product in enumerate(products, 1):
                print(f"\n{i}. {product.get('name', 'Unknown')}")
                print(f"   ID: {product.get('id', 'N/A')}")
                print(f"   Index: {product.get('idx_code', 'N/A')}")
                print(f"   Quantity: {product.get('quantity', 1)}")
                print(f"   Unit Price: {product.get('unit_price', 0):.2f} PLN")
                total = product.get('quantity', 1) * product.get('unit_price', 0)
                print(f"   Total: {total:.2f} PLN")

            total_value = sum(p.get('quantity', 1) * p.get('unit_price', 0) for p in products)
            print(f"\n=== TOTAL ORDER VALUE: {total_value:.2f} PLN ===\n")

        dialog = ProductSelectorDialog(
            root,
            db,
            existing_parts=[],
            callback=on_products_selected
        )

    # Add button to open dialog
    btn = ctk.CTkButton(
        root,
        text="Open Product Selector",
        command=open_selector,
        width=200,
        height=50
    )
    btn.pack(pady=50)

    # Info label
    info_label = ctk.CTkLabel(
        root,
        text="Click button to open enhanced product selector\nwith filters and inline editing",
        font=("Arial", 11)
    )
    info_label.pack()

    # Run
    root.mainloop()


if __name__ == "__main__":
    try:
        test_dialog()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)