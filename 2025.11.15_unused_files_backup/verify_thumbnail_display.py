#!/usr/bin/env python3
"""Verify thumbnail display in UI"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from products_module_enhanced import safe_decode_binary
from supabase import create_client
from dotenv import load_dotenv
from PIL import Image, ImageTk
import io

# Load environment variables
load_dotenv()

def create_test_window():
    """Create test window to display thumbnails"""

    print("="*60)
    print("TESTING THUMBNAIL DISPLAY IN UI")
    print("="*60)

    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
        return

    client = create_client(url, key)

    # Create test window
    root = ctk.CTk()
    root.title("Thumbnail Display Test")
    root.geometry("800x600")

    # Create scrollable frame
    scroll_frame = ctk.CTkScrollableFrame(root)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Fetch products with thumbnails
    print("\n1. Fetching products with thumbnails...")
    response = client.table('products_catalog').select("id, name, thumbnail_100").not_.is_('thumbnail_100', 'null').execute()

    if not response.data:
        label = ctk.CTkLabel(scroll_frame, text="No products with thumbnails found!")
        label.pack(pady=20)
        root.mainloop()
        return

    print(f"   Found {len(response.data)} products")

    # Display each product
    for i, product in enumerate(response.data, 1):
        print(f"\n2. Processing product {i}: {product['name']}")

        # Create frame for this product
        product_frame = ctk.CTkFrame(scroll_frame)
        product_frame.pack(fill="x", pady=5)

        # Product name
        name_label = ctk.CTkLabel(product_frame, text=f"Product: {product['name']}", font=("Arial", 14, "bold"))
        name_label.pack(side="left", padx=10)

        # Try different methods to display thumbnail
        thumbnail_data = product['thumbnail_100']

        # Method 1: Direct display with safe_decode_binary
        try:
            print(f"   Attempting Method 1: safe_decode_binary...")
            decoded = safe_decode_binary(thumbnail_data, "thumbnail_100")

            if decoded:
                print(f"   Decoded {len(decoded)} bytes")
                img = Image.open(io.BytesIO(decoded))
                print(f"   Image opened: {img.size}, mode={img.mode}")

                # Resize for display
                img.thumbnail((60, 40), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)

                # Display
                thumb_label1 = ctk.CTkLabel(product_frame, text="", image=photo, width=60, height=40)
                thumb_label1.image = photo  # Keep reference
                thumb_label1.pack(side="left", padx=5)

                status1 = ctk.CTkLabel(product_frame, text="✓ Method 1: OK", text_color="green")
                status1.pack(side="left", padx=5)

                print(f"   [OK] Method 1 successful")
            else:
                print(f"   [FAIL] Method 1: Could not decode")
                status1 = ctk.CTkLabel(product_frame, text="✗ Method 1: Failed", text_color="red")
                status1.pack(side="left", padx=5)

        except Exception as e:
            print(f"   [ERROR] Method 1 failed: {e}")
            status1 = ctk.CTkLabel(product_frame, text=f"✗ Method 1: {str(e)[:30]}", text_color="red")
            status1.pack(side="left", padx=5)

        # Method 2: Using CTkImage
        try:
            print(f"   Attempting Method 2: CTkImage...")
            decoded = safe_decode_binary(thumbnail_data, "thumbnail_100")

            if decoded:
                img = Image.open(io.BytesIO(decoded))

                # Create CTkImage
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 40))

                # Display
                thumb_label2 = ctk.CTkLabel(product_frame, text="", image=ctk_image, width=60, height=40)
                thumb_label2.pack(side="left", padx=5)

                status2 = ctk.CTkLabel(product_frame, text="✓ Method 2: OK", text_color="green")
                status2.pack(side="left", padx=5)

                print(f"   [OK] Method 2 successful")
            else:
                print(f"   [FAIL] Method 2: Could not decode")
                status2 = ctk.CTkLabel(product_frame, text="✗ Method 2: Failed", text_color="red")
                status2.pack(side="left", padx=5)

        except Exception as e:
            print(f"   [ERROR] Method 2 failed: {e}")
            status2 = ctk.CTkLabel(product_frame, text=f"✗ Method 2: {str(e)[:30]}", text_color="red")
            status2.pack(side="left", padx=5)

    print("\n" + "="*60)
    print("UI TEST WINDOW CREATED")
    print("Check if thumbnails are visible in the window")
    print("="*60)

    # Run the window
    root.mainloop()


if __name__ == "__main__":
    try:
        create_test_window()
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)