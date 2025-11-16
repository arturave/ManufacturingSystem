#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that product URL fields are properly loaded during edit
"""

import sys
import os
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from typing import Dict
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path for imports
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


def test_product_data_retrieval():
    """Test if product data is correctly retrieved with URL fields"""
    print("="*70)
    print("TESTING PRODUCT DATA RETRIEVAL WITH URL FIELDS")
    print("="*70)

    # Initialize database connection
    db = SimpleDB()

    # Get latest product with files
    response = db.client.table('products_catalog').select(
        """
        id,
        idx_code,
        name,
        cad_2d_url,
        cad_2d_filename,
        cad_3d_url,
        cad_3d_filename,
        user_image_url,
        user_image_filename,
        thumbnail_100_url,
        preview_800_url,
        preview_4k_url,
        additional_documentation_url
        """
    ).eq('is_active', True).order('created_at', desc=True).limit(1).execute()

    if not response.data:
        print("\n❌ No products found in database!")
        return

    product = response.data[0]
    print(f"\n✅ Found product: {product['name']} ({product['idx_code']})")
    print(f"   ID: {product['id']}")

    # Check URL fields
    print("\n📁 File URLs in database:")
    print(f"   - cad_2d_url: {'✅ Present' if product.get('cad_2d_url') else '❌ Missing'}")
    if product.get('cad_2d_url'):
        print(f"     URL: {product['cad_2d_url'][:100]}...")

    print(f"   - cad_3d_url: {'✅ Present' if product.get('cad_3d_url') else '❌ Missing'}")
    if product.get('cad_3d_url'):
        print(f"     URL: {product['cad_3d_url'][:100]}...")

    print(f"   - user_image_url: {'✅ Present' if product.get('user_image_url') else '❌ Missing'}")
    if product.get('user_image_url'):
        print(f"     URL: {product['user_image_url'][:100]}...")

    print(f"   - thumbnail_100_url: {'✅ Present' if product.get('thumbnail_100_url') else '❌ Missing'}")
    if product.get('thumbnail_100_url'):
        print(f"     URL: {product['thumbnail_100_url'][:100]}...")

    # Test if URLs are accessible
    if product.get('thumbnail_100_url'):
        print("\n🌐 Testing URL accessibility...")
        try:
            import requests
            response = requests.get(product['thumbnail_100_url'], timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Thumbnail URL is accessible (downloaded {len(response.content)} bytes)")
                # Check if it's a valid image
                from PIL import Image
                import io
                try:
                    img = Image.open(io.BytesIO(response.content))
                    print(f"   ✅ Valid image: {img.format} {img.size[0]}x{img.size[1]}")
                except Exception as e:
                    print(f"   ❌ Not a valid image: {e}")
            else:
                print(f"   ❌ HTTP {response.status_code} when accessing thumbnail URL")
        except Exception as e:
            print(f"   ❌ Error accessing URL: {e}")

    # Now test with full select (as done in products_module_enhanced.py)
    print("\n📋 Testing full product select (with joins)...")
    response2 = db.client.table('products_catalog').select(
        """
        *,
        materials_dict!material_id(name, category),
        customers!customer_id(name, short_name)
        """
    ).eq('id', product['id']).single().execute()

    full_product = response2.data
    print(f"   Full product keys count: {len(full_product.keys())}")

    # Check if URL fields are present in full select
    url_fields = ['cad_2d_url', 'cad_3d_url', 'user_image_url', 'thumbnail_100_url', 'preview_800_url', 'preview_4k_url']
    missing_fields = []
    present_fields = []

    for field in url_fields:
        if field in full_product:
            present_fields.append(field)
            if full_product[field]:
                print(f"   ✅ {field}: Present with value")
            else:
                print(f"   ⚠️ {field}: Present but NULL")
        else:
            missing_fields.append(field)
            print(f"   ❌ {field}: NOT in response keys!")

    print(f"\n📊 Summary:")
    print(f"   Present fields: {len(present_fields)}/{len(url_fields)}")
    print(f"   Missing fields: {len(missing_fields)}/{len(url_fields)}")

    if missing_fields:
        print(f"\n⚠️ PROBLEM FOUND: The following URL fields are missing from the full select:")
        for field in missing_fields:
            print(f"   - {field}")
        print("\n   This suggests the database schema might be missing these columns.")
        print("   Run REBUILD_PRODUCTS_CATALOG_FIXED.sql to fix the schema.")


if __name__ == "__main__":
    try:
        test_product_data_retrieval()
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)