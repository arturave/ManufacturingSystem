#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file loading logic without GUI
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# Fix Windows paths
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()


class SimpleDB:
    """Simple database connection for testing"""
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("No Supabase config! Check .env file")

        self.client: Client = create_client(self.url, self.key)


def test_file_loading():
    """Test file loading logic"""
    print("\n" + "="*70)
    print("TESTING FILE LOADING FROM SUPABASE STORAGE")
    print("="*70)

    # Initialize database
    db = SimpleDB()

    # Get a product with files
    response = db.client.table('products_catalog').select(
        """
        id,
        name,
        idx_code,
        cad_2d_url,
        cad_2d_filename,
        cad_3d_url,
        cad_3d_filename,
        thumbnail_100_url
        """
    ).not_.is_('cad_3d_url', 'null').eq('is_active', True).order('created_at', desc=True).limit(1).execute()

    if not response.data:
        print("\n[ERROR] No products with files found!")
        return

    product = response.data[0]
    print(f"\nProduct: {product['name']} ({product['idx_code']})")
    print(f"ID: {product['id']}")

    # Test loading CAD 3D file
    if product.get('cad_3d_url'):
        print(f"\n[TEST] Loading CAD 3D file...")
        print(f"URL: {product['cad_3d_url']}")
        print(f"Filename: {product.get('cad_3d_filename', 'unknown')}")

        try:
            # Download the file
            print(f"Making HTTP request...")
            response = requests.get(product['cad_3d_url'], timeout=10)
            print(f"Response status: {response.status_code}")
            print(f"Response headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")

            if response.status_code == 200:
                content = response.content
                print(f"\n[SUCCESS] Downloaded {len(content)} bytes")
                print(f"First 100 bytes: {content[:100]}")

                # Check if it looks like a valid STEP file
                if product.get('cad_3d_filename', '').lower().endswith(('.stp', '.step')):
                    header = content[:100].decode('ascii', errors='ignore')
                    if 'ISO-10303' in header:
                        print("[OK] Valid STEP file header detected")
                    else:
                        print("[WARNING] Doesn't look like a valid STEP file")
                        print(f"Header: {header}")
            else:
                print(f"[ERROR] Failed to download: HTTP {response.status_code}")
                print(f"Response text: {response.text[:500]}")

        except Exception as e:
            print(f"[ERROR] Exception during download: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[INFO] No CAD 3D URL in product data")

    # Test loading thumbnail
    if product.get('thumbnail_100_url'):
        print(f"\n[TEST] Loading thumbnail...")
        print(f"URL: {product['thumbnail_100_url']}")

        try:
            response = requests.get(product['thumbnail_100_url'], timeout=5)
            if response.status_code == 200:
                print(f"[SUCCESS] Downloaded {len(response.content)} bytes")

                # Try to verify it's an image
                from PIL import Image
                import io
                try:
                    img = Image.open(io.BytesIO(response.content))
                    print(f"[OK] Valid {img.format} image, size: {img.size}")
                except Exception as e:
                    print(f"[WARNING] Not a valid image: {e}")
            else:
                print(f"[ERROR] Failed to download: HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Exception during thumbnail download: {e}")
    else:
        print("\n[INFO] No thumbnail URL in product data")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_file_loading()