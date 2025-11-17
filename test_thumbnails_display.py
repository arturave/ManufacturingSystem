#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for verifying thumbnail display in product lists
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import base64

# Load environment variables
load_dotenv()

def fix_base64_padding(data):
    """Fix base64 string padding"""
    padding = len(data) % 4
    if padding:
        data += '=' * (4 - padding)
    return data

def get_thumbnail_from_product(product):
    """Extract thumbnail from product data"""
    try:
        # Check for preview_800_url as data URL
        if product.get('preview_800_url'):
            preview_url = product['preview_800_url']
            if isinstance(preview_url, str) and preview_url.startswith('data:image'):
                # Extract base64 from data URL
                base64_data = preview_url.split(',')[1] if ',' in preview_url else preview_url
                image_data = base64.b64decode(fix_base64_padding(base64_data))
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((50, 50), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)

        # Check for thumbnail_100_url
        if product.get('thumbnail_100_url'):
            # This would need URL loading implementation
            print(f"Product {product.get('name')} has thumbnail_100_url but not data URL")

        return None

    except Exception as e:
        print(f"Error loading thumbnail for {product.get('name', 'unknown')}: {e}")
        return None

def test_thumbnails():
    """Test thumbnail loading and display"""

    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        return

    client = create_client(url, key)

    # Create test window
    root = tk.Tk()
    root.title("Test Thumbnail Display")
    root.geometry("1200x600")

    # Create frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Create treeview with thumbnail column
    tree = ttk.Treeview(
        main_frame,
        columns=('name', 'idx_code', 'material', 'thickness', 'has_thumbnail'),
        show='tree headings',
        height=20
    )

    # Configure columns
    tree.heading('#0', text='Miniatura')
    tree.heading('name', text='Nazwa')
    tree.heading('idx_code', text='Indeks')
    tree.heading('material', text='Materiał')
    tree.heading('thickness', text='Grubość')
    tree.heading('has_thumbnail', text='Ma miniaturę?')

    tree.column('#0', width=80, stretch=False)
    tree.column('name', width=300)
    tree.column('idx_code', width=150)
    tree.column('material', width=150)
    tree.column('thickness', width=100)
    tree.column('has_thumbnail', width=120)

    # Scrollbars
    vscroll = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
    hscroll = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    # Grid layout
    tree.grid(row=0, column=0, sticky="nsew")
    vscroll.grid(row=0, column=1, sticky="ns")
    hscroll.grid(row=1, column=0, sticky="ew")

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    # Info label
    info_label = ttk.Label(root, text="Ładowanie produktów...")
    info_label.pack(pady=5)

    # Store thumbnails to prevent garbage collection
    thumbnails = []

    # Load products
    try:
        print("Fetching products from database...")
        response = client.table('products_catalog').select(
            '*',
            'materials_dict(name)',
            'customers(name, short_name)'
        ).eq('is_active', True).limit(50).execute()

        products = response.data
        print(f"Loaded {len(products)} products")

        # Stats
        products_with_thumbnails = 0
        products_without_thumbnails = 0

        # Add products to tree
        for product in products:
            # Get thumbnail
            thumbnail = get_thumbnail_from_product(product)
            if thumbnail:
                thumbnails.append(thumbnail)  # Keep reference
                products_with_thumbnails += 1
                has_thumb = "TAK ✓"
            else:
                products_without_thumbnails += 1
                has_thumb = "NIE ✗"

            # Get material name
            material = ""
            if product.get('materials_dict'):
                material = product['materials_dict'].get('name', '')

            # Insert into tree
            tree.insert('', 'end',
                image=thumbnail if thumbnail else '',
                values=(
                    product.get('name', ''),
                    product.get('idx_code', ''),
                    material,
                    f"{product.get('thickness_mm', '')} mm" if product.get('thickness_mm') else '',
                    has_thumb
                )
            )

        # Update info
        info_text = (f"Załadowano {len(products)} produktów | "
                    f"Z miniaturami: {products_with_thumbnails} | "
                    f"Bez miniatur: {products_without_thumbnails}")
        info_label.config(text=info_text)

        print(f"\nStatistics:")
        print(f"  Products with thumbnails: {products_with_thumbnails}")
        print(f"  Products without thumbnails: {products_without_thumbnails}")

        # Analyze thumbnail data
        print(f"\nAnalyzing thumbnail fields:")
        for i, product in enumerate(products[:5]):  # Check first 5
            print(f"\nProduct {i+1}: {product.get('name', 'unknown')}")
            print(f"  - has preview_800_url: {bool(product.get('preview_800_url'))}")
            if product.get('preview_800_url'):
                url = product['preview_800_url']
                if isinstance(url, str):
                    print(f"    - is data URL: {url.startswith('data:image')}")
                    print(f"    - length: {len(url)} chars")
            print(f"  - has thumbnail_100_url: {bool(product.get('thumbnail_100_url'))}")

    except Exception as e:
        print(f"Error loading products: {e}")
        info_label.config(text=f"Błąd: {e}")

    # Button frame
    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)

    # Refresh button
    def refresh():
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        thumbnails.clear()
        # Reload
        test_thumbnails()

    ttk.Button(btn_frame, text="Odśwież", command=refresh).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Zamknij", command=root.quit).pack(side="left", padx=5)

    # Run
    root.mainloop()

if __name__ == "__main__":
    print("Starting thumbnail display test...")
    test_thumbnails()