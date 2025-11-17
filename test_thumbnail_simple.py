#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple console test for thumbnail loading
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from thumbnail_loader import ThumbnailLoader

# Load environment variables
load_dotenv()

def test():
    """Simple test of thumbnail loader"""

    print("Testing Thumbnail Loader")
    print("=" * 60)

    # Initialize Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("[ERROR] Missing SUPABASE credentials")
        return

    client = create_client(url, key)

    # Initialize loader
    print("Initializing ThumbnailLoader...")
    loader = ThumbnailLoader()

    # Get one product with thumbnail
    print("Fetching product with thumbnail...")
    response = client.table('products_catalog').select(
        'name, preview_800_url, thumbnail_100_url'
    ).not_.is_('preview_800_url', 'null').limit(1).execute()

    if not response.data:
        print("[ERROR] No products with thumbnails found")
        return

    product = response.data[0]
    print(f"Product: {product['name']}")

    # Test loading
    url = product.get('preview_800_url') or product.get('thumbnail_100_url')

    if url:
        print(f"URL type: {'HTTP' if url.startswith('http') else 'Unknown'}")
        print(f"URL length: {len(url)} chars")

        # Try to load
        print("Loading thumbnail...")
        try:
            data = loader.load_from_http_url(url)

            if data:
                print(f"[SUCCESS] Loaded {len(data)} bytes")

                # Try to create image
                from PIL import Image
                import io

                img = Image.open(io.BytesIO(data))
                print(f"[SUCCESS] Image: {img.size[0]}x{img.size[1]} {img.mode}")

                # Test get_thumbnail method
                thumb = loader.get_thumbnail(url, size=(40, 40), as_photo_image=False)
                if thumb:
                    print(f"[SUCCESS] Thumbnail: {thumb.size[0]}x{thumb.size[1]}")
                else:
                    print("[FAILED] Could not create thumbnail")

            else:
                print("[FAILED] No data loaded")

        except Exception as e:
            print(f"[ERROR] {e}")

    else:
        print("[ERROR] No URL found")

if __name__ == "__main__":
    test()