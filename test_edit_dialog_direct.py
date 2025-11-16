#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test of the EnhancedPartEditDialog to debug file loading
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import customtkinter as ctk

# Fix Windows paths
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from part_edit_enhanced_v4 import EnhancedPartEditDialogV4


class SimpleDB:
    """Simple database connection for testing"""
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("No Supabase config! Check .env file")

        self.client: Client = create_client(self.url, self.key)


def test_edit_dialog():
    """Test the edit dialog with a product from the database"""
    print("\n" + "="*70)
    print("TESTING ENHANCED PART EDIT DIALOG - FILE LOADING")
    print("="*70)

    # Initialize database
    db = SimpleDB()

    # Get a product with files
    response = db.client.table('products_catalog').select(
        """
        *,
        materials_dict!material_id(name, category),
        customers!customer_id(name, short_name)
        """
    ).not_.is_('cad_3d_url', 'null').eq('is_active', True).order('created_at', desc=True).limit(1).execute()

    if not response.data:
        print("\n[ERROR] No products with files found in database!")
        return

    product = response.data[0]
    print(f"\nFound product: {product['name']} ({product['idx_code']})")
    print(f"Product ID: {product['id']}")

    # Check what URL fields are present
    print("\n[URL FIELDS] in product data:")
    url_fields = ['cad_2d_url', 'cad_3d_url', 'user_image_url', 'thumbnail_100_url', 'preview_800_url', 'preview_4k_url']
    for field in url_fields:
        value = product.get(field)
        if value:
            print(f"  [OK] {field}: {value[:80]}...")
        else:
            print(f"  [MISSING] {field}: None")

    print("\n" + "="*70)
    print("Opening Edit Dialog - Watch for debug output...")
    print("="*70 + "\n")

    # Create root window
    root = ctk.CTk()
    root.withdraw()  # Hide main window

    # Open edit dialog
    dialog = EnhancedPartEditDialogV4(
        root,
        db,
        [],
        part_data=product,
        part_index=None,
        order_id=None,
        catalog_mode=True,
        title="Test Edit Product"
    )

    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    try:
        test_edit_dialog()
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()