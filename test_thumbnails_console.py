#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console test for checking thumbnail data in products
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_product_thumbnails():
    """Test if products have thumbnail data"""

    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        return

    print("Connecting to Supabase...")
    client = create_client(url, key)

    try:
        # Fetch products
        print("Fetching products from database...")
        response = client.table('products_catalog').select(
            'id, name, idx_code, preview_800_url, thumbnail_100_url'
        ).limit(20).execute()

        products = response.data
        print(f"\n[OK] Loaded {len(products)} products\n")

        # Analyze thumbnail data
        products_with_preview = 0
        products_with_thumbnail = 0
        products_with_data_url = 0
        products_without_any = 0

        print("=" * 80)
        print("PRODUCT THUMBNAIL ANALYSIS")
        print("=" * 80)

        for i, product in enumerate(products):
            print(f"\n{i+1}. {product.get('name', 'Unknown')} (ID: {product.get('id', 'N/A')})")
            print(f"   Index: {product.get('idx_code', 'N/A')}")

            has_thumbnail = False

            # Check preview_800_url
            if product.get('preview_800_url'):
                preview = product['preview_800_url']
                products_with_preview += 1
                has_thumbnail = True

                if isinstance(preview, str):
                    if preview.startswith('data:image'):
                        products_with_data_url += 1
                        print(f"   [Y] Has preview_800_url (data URL, {len(preview)} chars)")
                    elif preview.startswith('http'):
                        print(f"   [Y] Has preview_800_url (HTTP URL)")
                    else:
                        print(f"   [Y] Has preview_800_url (unknown format)")
                else:
                    print(f"   [Y] Has preview_800_url (non-string)")
            else:
                print(f"   [N] No preview_800_url")

            # Check thumbnail_100_url
            if product.get('thumbnail_100_url'):
                products_with_thumbnail += 1
                has_thumbnail = True
                thumb = product['thumbnail_100_url']

                if isinstance(thumb, str):
                    if thumb.startswith('data:image'):
                        print(f"   [Y] Has thumbnail_100_url (data URL, {len(thumb)} chars)")
                    elif thumb.startswith('http'):
                        print(f"   [Y] Has thumbnail_100_url (HTTP URL)")
                    else:
                        print(f"   [Y] Has thumbnail_100_url (unknown format)")
                else:
                    print(f"   [Y] Has thumbnail_100_url (non-string)")
            else:
                print(f"   [N] No thumbnail_100_url")

            if not has_thumbnail:
                products_without_any += 1

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total products checked: {len(products)}")
        print(f"Products with preview_800_url: {products_with_preview} ({products_with_preview*100/len(products):.1f}%)")
        print(f"Products with data URL preview: {products_with_data_url} ({products_with_data_url*100/len(products):.1f}%)")
        print(f"Products with thumbnail_100_url: {products_with_thumbnail} ({products_with_thumbnail*100/len(products):.1f}%)")
        print(f"Products without any thumbnail: {products_without_any} ({products_without_any*100/len(products):.1f}%)")

        # Test parts table
        print("\n" + "=" * 80)
        print("TESTING PARTS TABLE")
        print("=" * 80)

        # Get sample order with parts
        orders_response = client.table('orders').select('id, title').limit(1).execute()

        if orders_response.data:
            order = orders_response.data[0]
            print(f"Testing parts for order: {order['title']} (ID: {order['id']})")

            # Get parts with product join
            parts_response = client.table('parts').select(
                '*',
                'products_catalog(preview_800_url, thumbnail_100_url)'
            ).eq('order_id', order['id']).execute()

            parts = parts_response.data
            print(f"Found {len(parts)} parts")

            for part in parts[:5]:  # Show first 5
                print(f"\n  Part: {part.get('name', 'Unknown')}")
                if part.get('products_catalog'):
                    print(f"    [Y] Has linked product")
                    product = part['products_catalog']
                    if product.get('preview_800_url'):
                        print(f"      [Y] Product has preview_800_url")
                    else:
                        print(f"      [N] Product missing preview_800_url")
                else:
                    print(f"    [N] No linked product")
        else:
            print("No orders found to test parts")

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_product_thumbnails()