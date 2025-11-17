#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test thumbnail loading from HTTP URLs
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import tkinter as tk
from tkinter import ttk
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thumbnail_loader import ThumbnailLoader

# Load environment variables
load_dotenv()

def test_http_thumbnails():
    """Test loading thumbnails from HTTP URLs"""

    print("=" * 80)
    print("TESTING HTTP THUMBNAIL LOADING")
    print("=" * 80)

    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        return

    print("Connecting to Supabase...")
    client = create_client(url, key)

    # Initialize thumbnail loader
    print("Initializing thumbnail loader...")
    loader = ThumbnailLoader()

    try:
        # Fetch products with thumbnails
        print("Fetching products with thumbnails...")
        response = client.table('products_catalog').select(
            'id, name, idx_code, preview_800_url, thumbnail_100_url'
        ).not_.is_('preview_800_url', 'null').limit(5).execute()

        products = response.data
        print(f"Found {len(products)} products with thumbnails\n")

        if not products:
            print("[WARNING] No products with thumbnails found in database")
            return

        # Create test window
        root = tk.Tk()
        root.title("HTTP Thumbnail Test")
        root.geometry("800x600")

        # Create frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create treeview
        tree = ttk.Treeview(
            main_frame,
            columns=('name', 'idx_code', 'status', 'load_time'),
            show='tree headings',
            height=15
        )

        tree.heading('#0', text='Miniatura')
        tree.heading('name', text='Nazwa')
        tree.heading('idx_code', text='Indeks')
        tree.heading('status', text='Status')
        tree.heading('load_time', text='Czas [ms]')

        tree.column('#0', width=80, stretch=False)
        tree.column('name', width=250)
        tree.column('idx_code', width=150)
        tree.column('status', width=150)
        tree.column('load_time', width=100)

        tree.pack(fill="both", expand=True)

        # Info label
        info_label = ttk.Label(root, text="Testing thumbnail loading...")
        info_label.pack(pady=5)

        # Store thumbnails
        thumbnails = []

        # Process each product
        successful = 0
        failed = 0

        for i, product in enumerate(products):
            print(f"\nTesting product {i+1}/{len(products)}: {product['name']}")

            # Try loading thumbnail
            start_time = time.time()
            status = "Failed"
            load_time = 0

            # Try preview_800_url first
            thumbnail_url = product.get('preview_800_url') or product.get('thumbnail_100_url')

            if thumbnail_url:
                print(f"  URL: {thumbnail_url[:80]}...")

                try:
                    thumbnail = loader.get_thumbnail(thumbnail_url, size=(40, 40), as_photo_image=True)

                    if thumbnail:
                        thumbnails.append(thumbnail)
                        status = "Success"
                        successful += 1
                        print(f"  [SUCCESS] Thumbnail loaded")
                    else:
                        failed += 1
                        print(f"  [FAILED] Could not create thumbnail")

                except Exception as e:
                    failed += 1
                    print(f"  [ERROR] {e}")
                    thumbnail = None

            else:
                print(f"  [SKIP] No thumbnail URL")
                thumbnail = None

            load_time = int((time.time() - start_time) * 1000)

            # Add to tree
            tree.insert('', 'end',
                image=thumbnail if thumbnail else '',
                values=(
                    product['name'],
                    product['idx_code'],
                    status,
                    f"{load_time} ms"
                )
            )

            # Update display
            root.update()

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total products tested: {len(products)}")
        print(f"Successful loads: {successful}")
        print(f"Failed loads: {failed}")
        print(f"Success rate: {successful*100/len(products):.1f}%")

        # Update info
        info_label.config(text=f"Test complete. Success: {successful}/{len(products)} ({successful*100/len(products):.0f}%)")

        # Test cache
        if successful > 0:
            print("\n" + "=" * 80)
            print("TESTING CACHE")
            print("=" * 80)

            first_product = products[0]
            url = first_product.get('preview_800_url') or first_product.get('thumbnail_100_url')

            if url:
                # Load without cache
                print("Loading without cache...")
                start = time.time()
                loader2 = ThumbnailLoader()
                thumb1 = loader2.load_from_http_url(url, use_cache=False)
                time_no_cache = time.time() - start
                print(f"  Time: {time_no_cache*1000:.2f} ms")

                # Load with cache (should be faster)
                print("Loading with cache...")
                start = time.time()
                thumb2 = loader.load_from_http_url(url, use_cache=True)
                time_with_cache = time.time() - start
                print(f"  Time: {time_with_cache*1000:.2f} ms")

                if time_with_cache < time_no_cache:
                    print(f"  [SUCCESS] Cache is {time_no_cache/time_with_cache:.1f}x faster")
                else:
                    print(f"  [INFO] Cache not faster (first load may have warmed up connection)")

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)

        def close():
            root.quit()
            root.destroy()

        ttk.Button(btn_frame, text="Zamknij", command=close).pack()

        # Run
        root.mainloop()

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_http_thumbnails()