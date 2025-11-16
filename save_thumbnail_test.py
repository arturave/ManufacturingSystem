#!/usr/bin/env python3
"""Save thumbnail_100 from database as PNG file for testing"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from products_module_enhanced import safe_decode_binary
from supabase import create_client
from dotenv import load_dotenv
from PIL import Image
import io
from datetime import datetime

# Load environment variables
load_dotenv()

def save_thumbnail_as_png():
    """Extract thumbnail from database and save as PNG"""

    print("="*60)
    print("SAVING THUMBNAIL_100 AS PNG FILE")
    print("="*60)

    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
        return False

    client = create_client(url, key)

    # Fetch products with thumbnails
    print("\n1. Fetching products with thumbnails...")
    response = client.table('products_catalog').select("id, name, thumbnail_100").not_.is_('thumbnail_100', 'null').execute()

    if not response.data:
        print("   No products with thumbnails found!")
        return False

    # Create screenshots folder if it doesn't exist
    screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)
    print(f"\n2. Screenshots directory: {screenshots_dir}")

    # Process each product
    for i, product in enumerate(response.data, 1):
        print(f"\n3. Processing product {i}: {product['name']}")
        print(f"   ID: {product['id']}")

        thumbnail_data = product['thumbnail_100']

        # Check data type
        print(f"   Raw data type: {type(thumbnail_data).__name__}")
        if isinstance(thumbnail_data, str):
            print(f"   String length: {len(thumbnail_data)}")
            print(f"   First 50 chars: {thumbnail_data[:50]}...")

        # Decode using our function
        print("\n   Decoding thumbnail data...")
        decoded = safe_decode_binary(thumbnail_data, "thumbnail_100")

        if not decoded:
            print("   [FAIL] Could not decode thumbnail data")
            continue

        print(f"   [OK] Decoded to {len(decoded)} bytes")

        # Check if it's a valid image
        if decoded[:8] == b'\x89PNG\r\n\x1a\n':
            print("   [OK] Valid PNG signature detected")
        elif decoded[:3] == b'\xff\xd8\xff':
            print("   [OK] Valid JPEG signature detected")
        else:
            print(f"   [WARNING] Unknown format, first 8 bytes: {decoded[:8].hex()}")

        # Try to open as image
        try:
            img = Image.open(io.BytesIO(decoded))
            print(f"   [OK] Image opened: {img.size[0]}x{img.size[1]}, mode={img.mode}")

            # Save as PNG
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thumbnail_{product['name']}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)

            img.save(filepath, 'PNG')
            print(f"   [OK] Saved as: {filepath}")

            # Also save the raw decoded bytes for verification
            raw_filename = f"thumbnail_{product['name']}_{timestamp}_raw.bin"
            raw_filepath = os.path.join(screenshots_dir, raw_filename)
            with open(raw_filepath, 'wb') as f:
                f.write(decoded)
            print(f"   [OK] Raw bytes saved as: {raw_filepath}")

        except Exception as e:
            print(f"   [FAIL] Error processing image: {e}")

            # Try to save raw bytes anyway
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_filename = f"thumbnail_{product['name']}_{timestamp}_ERROR.bin"
            error_filepath = os.path.join(screenshots_dir, error_filename)
            with open(error_filepath, 'wb') as f:
                f.write(decoded)
            print(f"   [INFO] Raw bytes saved for debugging: {error_filepath}")

    print("\n" + "="*60)
    print("COMPLETED")
    print(f"Check the '{screenshots_dir}' folder for saved thumbnails")
    print("="*60)

    return True


if __name__ == "__main__":
    try:
        success = save_thumbnail_as_png()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)