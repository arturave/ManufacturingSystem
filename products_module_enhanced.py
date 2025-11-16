#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Products Management Module
Comprehensive product/parts management with improved UI and database integration
"""

import customtkinter as ctk
from tkinter import messagebox, Menu
import tkinter as tk
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import io
import base64
import uuid
import getpass
from pathlib import Path

from image_processing import ImageProcessor, get_cached_image
from materials_dict_module import MaterialsDictDialog
# Import the enhanced V4 version
from part_edit_enhanced_v4 import EnhancedPartEditDialogV4 as EnhancedPartEditDialog

# For backward compatibility
__all__ = ['EnhancedPartEditDialog']

from integrated_viewer_v2 import ThumbnailGenerator
from storage_utils import upload_product_file, DEFAULT_BUCKET


def fix_base64_padding(data: str) -> str:
    """Fix base64 string padding if needed"""
    if not data:
        return data

    # Remove any whitespace or newlines
    data = data.strip()

    # Remove any existing padding first
    data = data.rstrip('=')

    # Add correct padding
    padding_needed = len(data) % 4
    if padding_needed:
        data += '=' * (4 - padding_needed)

    return data

def generate_thumbnails_from_image(image_data: bytes) -> dict:
    """
    Generate thumbnails from image data
    Returns dict with thumbnail_100, preview_800, preview_4k as bytes
    """
    try:
        from PIL import Image
        import io

        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        result = {}

        # Generate thumbnail 100x100
        thumb_100 = img.copy()
        thumb_100.thumbnail((100, 100), Image.Resampling.LANCZOS)
        thumb_100_bytes = io.BytesIO()
        thumb_100.save(thumb_100_bytes, format='PNG')
        result['thumbnail_100'] = thumb_100_bytes.getvalue()

        # Generate preview 800px
        preview_800 = img.copy()
        preview_800.thumbnail((800, 800), Image.Resampling.LANCZOS)
        preview_800_bytes = io.BytesIO()
        preview_800.save(preview_800_bytes, format='PNG')
        result['preview_800'] = preview_800_bytes.getvalue()

        # Generate preview 4K (3840x2160 max)
        preview_4k = img.copy()
        preview_4k.thumbnail((3840, 2160), Image.Resampling.LANCZOS)
        preview_4k_bytes = io.BytesIO()
        preview_4k.save(preview_4k_bytes, format='PNG')
        result['preview_4k'] = preview_4k_bytes.getvalue()

        print(f"DEBUG: Generated thumbnails - sizes: 100px={len(result['thumbnail_100'])} bytes, "
              f"800px={len(result['preview_800'])} bytes, 4K={len(result['preview_4k'])} bytes")

        return result
    except Exception as e:
        print(f"Error generating thumbnails: {e}")
        return {}

def safe_decode_binary(data, field_name="data"):
    """Safely decode binary data from various formats

    Handles double encoding (hex->base64->binary) from Supabase

    Args:
        data: Can be bytes, bytearray, memoryview, hex string, or base64 string
        field_name: Name of the field for error messages

    Returns:
        bytes: The binary data or None if decoding failed
    """
    import re  # Import at function level to ensure availability

    if not data:
        return None

    # Reduced debug - only show for thumbnails
    debug_enabled = "thumbnail" in field_name.lower()

    if debug_enabled:
        print(f"DEBUG decode {field_name}: type={type(data).__name__}, len={len(data) if hasattr(data, '__len__') else 'N/A'}")

    try:
        # If it's already bytes, return as is
        if isinstance(data, bytes):
            if debug_enabled:
                print(f"DEBUG decode {field_name}: Already bytes, returning as-is")
            return data

        # If it's a bytearray or memoryview (from PostgreSQL bytea), convert to bytes
        if isinstance(data, (bytearray, memoryview)):
            if debug_enabled:
                print(f"DEBUG decode {field_name}: Converting bytearray/memoryview to bytes")
            return bytes(data)

        # If it's a string, determine format and decode
        if isinstance(data, str):
            # STEP 1: Handle hex encoding (Supabase returns bytea as hex, sometimes with \x prefix)
            hex_str = None

            if data.startswith('\\x'):
                # Remove the \x prefix and convert from hex
                hex_str = data[2:]  # Remove '\x' prefix
            else:
                # Check if it's a hex string without \x prefix (all hex characters)
                # Hex strings from PostgreSQL are typically even length
                if len(data) % 2 == 0 and re.match(r'^[0-9a-fA-F]+$', data[:min(100, len(data))]):
                    hex_str = data

            if hex_str:
                try:
                    decoded_data = bytes.fromhex(hex_str)

                    # STEP 2: Check if the result is base64 encoded
                    # (Our data is double-encoded: binary -> base64 -> hex)
                    try:
                        # Try to decode as ASCII (base64 is ASCII)
                        decoded_str = decoded_data.decode('ascii')

                        # Check if it looks like base64
                        if re.match(r'^[A-Za-z0-9+/\s]*=*$', decoded_str[:100]):
                            # Remove any whitespace/newlines
                            cleaned_base64 = decoded_str.replace('\n', '').replace('\r', '').replace(' ', '')
                            fixed_base64 = fix_base64_padding(cleaned_base64)
                            result = base64.b64decode(fixed_base64)

                            # Check if it's a valid image (PNG/JPEG signature)
                            if debug_enabled:
                                if result[:8] == b'\x89PNG\r\n\x1a\n':
                                    print(f"DEBUG: {field_name} decoded successfully - Valid PNG image, {len(result)} bytes")
                                elif result[:3] == b'\xff\xd8\xff':
                                    print(f"DEBUG: {field_name} decoded successfully - Valid JPEG image, {len(result)} bytes")
                                else:
                                    print(f"DEBUG: {field_name} decoded successfully - {len(result)} bytes")

                            return result
                    except UnicodeDecodeError:
                        # Not ASCII/base64, return hex-decoded data
                        pass
                    except Exception as e:
                        if debug_enabled:
                            print(f"DEBUG: {field_name} base64 decode failed: {e}")

                    # If not base64, return the hex-decoded data
                    return decoded_data
                except ValueError:
                    # Not valid hex, continue to try other formats
                    pass

            # Otherwise try base64
            try:
                # Try to fix padding and decode as base64
                fixed_base64 = fix_base64_padding(data)
                result = base64.b64decode(fixed_base64)
                return result
            except Exception:
                # If base64 fails, return None
                return None

    except Exception as e:
        if debug_enabled:
            print(f"ERROR decoding {field_name}: {str(e)}")
        return None

    return None


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for customizing product list appearance"""

    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.parent = parent
        self.settings = current_settings.copy()  # Work with copy
        self.result = None

        self.title("Ustawienia listy produktów")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 300
        y = (self.winfo_screenheight() // 2) - 250
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup settings UI"""
        # Main container
        main = ctk.CTkScrollableFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ctk.CTkLabel(
            main,
            text="⚙️ Ustawienia wyświetlania",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)

        # Row height setting
        ctk.CTkLabel(main, text="Wysokość wierszy:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10, 5))

        row_height_frame = ctk.CTkFrame(main)
        row_height_frame.pack(fill="x", pady=5)

        self.row_height_slider = ctk.CTkSlider(
            row_height_frame,
            from_=40,
            to=120,
            number_of_steps=40,
            command=self.update_row_height_label
        )
        self.row_height_slider.set(self.settings.get('row_height', 80))
        self.row_height_slider.pack(side="left", padx=5, fill="x", expand=True)

        self.row_height_label = ctk.CTkLabel(row_height_frame, text=f"{self.settings.get('row_height', 80)}px")
        self.row_height_label.pack(side="right", padx=10)

        # Show thumbnails toggle
        self.show_thumbnails_var = ctk.BooleanVar(value=self.settings.get('show_thumbnails', True))
        ctk.CTkCheckBox(
            main,
            text="Wyświetlaj miniatury",
            variable=self.show_thumbnails_var,
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=10)

        # Color settings
        ctk.CTkLabel(main, text="Kolory wierszy:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10, 5))

        color_frame = ctk.CTkFrame(main)
        color_frame.pack(fill="x", pady=5)

        # Even row color
        even_frame = ctk.CTkFrame(color_frame)
        even_frame.pack(side="left", padx=10)
        ctk.CTkLabel(even_frame, text="Wiersze parzyste:").pack()
        self.even_color_entry = ctk.CTkEntry(even_frame, width=100)
        self.even_color_entry.insert(0, self.settings.get('even_row_color', '#2b2b2b'))
        self.even_color_entry.pack()

        # Odd row color
        odd_frame = ctk.CTkFrame(color_frame)
        odd_frame.pack(side="left", padx=10)
        ctk.CTkLabel(odd_frame, text="Wiersze nieparzyste:").pack()
        self.odd_color_entry = ctk.CTkEntry(odd_frame, width=100)
        self.odd_color_entry.insert(0, self.settings.get('odd_row_color', '#252525'))
        self.odd_color_entry.pack()

        # Selected row color
        selected_frame = ctk.CTkFrame(color_frame)
        selected_frame.pack(side="left", padx=10)
        ctk.CTkLabel(selected_frame, text="Zaznaczony wiersz:").pack()
        self.selected_color_entry = ctk.CTkEntry(selected_frame, width=100)
        self.selected_color_entry.insert(0, self.settings.get('selected_row_color', '#3a5f8a'))
        self.selected_color_entry.pack()

        # Font size setting
        ctk.CTkLabel(main, text="Rozmiar czcionki:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(10, 5))

        font_frame = ctk.CTkFrame(main)
        font_frame.pack(fill="x", pady=5)

        self.font_size_slider = ctk.CTkSlider(
            font_frame,
            from_=10,
            to=18,
            number_of_steps=8,
            command=self.update_font_size_label
        )
        self.font_size_slider.set(self.settings.get('font_size', 12))
        self.font_size_slider.pack(side="left", padx=5, fill="x", expand=True)

        self.font_size_label = ctk.CTkLabel(font_frame, text=f"{self.settings.get('font_size', 12)}pt")
        self.font_size_label.pack(side="right", padx=10)

        # Auto-refresh setting
        self.auto_refresh_var = ctk.BooleanVar(value=self.settings.get('auto_refresh_on_edit', True))
        ctk.CTkCheckBox(
            main,
            text="Automatyczne odświeżanie po edycji",
            variable=self.auto_refresh_var,
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", side="bottom", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="💾 Zapisz",
            command=self.save_settings,
            fg_color="#4CAF50"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="↺ Przywróć domyślne",
            command=self.reset_to_defaults,
            fg_color="#FF9800"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="❌ Anuluj",
            command=self.cancel,
            fg_color="#757575"
        ).pack(side="right", padx=5)

    def update_row_height_label(self, value):
        """Update row height label"""
        self.row_height_label.configure(text=f"{int(value)}px")

    def update_font_size_label(self, value):
        """Update font size label"""
        self.font_size_label.configure(text=f"{int(value)}pt")

    def save_settings(self):
        """Save settings and close dialog"""
        self.settings['row_height'] = int(self.row_height_slider.get())
        self.settings['show_thumbnails'] = self.show_thumbnails_var.get()
        self.settings['even_row_color'] = self.even_color_entry.get()
        self.settings['odd_row_color'] = self.odd_color_entry.get()
        self.settings['selected_row_color'] = self.selected_color_entry.get()
        self.settings['font_size'] = int(self.font_size_slider.get())
        self.settings['auto_refresh_on_edit'] = self.auto_refresh_var.get()

        self.result = self.settings
        self.destroy()

    def reset_to_defaults(self):
        """Reset to default settings"""
        self.row_height_slider.set(80)
        self.show_thumbnails_var.set(True)
        self.even_color_entry.delete(0, "end")
        self.even_color_entry.insert(0, "#2b2b2b")
        self.odd_color_entry.delete(0, "end")
        self.odd_color_entry.insert(0, "#252525")
        self.selected_color_entry.delete(0, "end")
        self.selected_color_entry.insert(0, "#3a5f8a")
        self.font_size_slider.set(12)
        self.auto_refresh_var.set(True)

    def cancel(self):
        """Cancel without saving"""
        self.result = None
        self.destroy()


class EnhancedProductsWindow(ctk.CTkToplevel):
    """Enhanced products management window with better UI and functionality"""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.products_data = []
        self.filtered_products = []
        self.selected_product = None
        self.selected_row_frame = None

        # Cache for thumbnails
        self.thumbnail_cache = {}

        # Load user preferences
        self.settings = self.load_settings()

        self.title("Zarządzanie produktami (katalog)")
        self.geometry("1500x850")

        # Make modal
        self.transient(parent)

        self.setup_ui()
        self.load_products()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 750
        y = (self.winfo_screenheight() // 2) - 425
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup enhanced UI components"""
        # Header with better styling
        header = ctk.CTkFrame(self, fg_color="#1e1e1e", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Title on left
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="KATALOG PRODUKTÓW",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Zarządzanie produktami w katalogu",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w")

        # Header buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)

        ctk.CTkButton(
            btn_frame,
            text="➕ Dodaj produkt",
            width=140,
            height=40,
            command=self.add_product,
            fg_color="#4CAF50",
            hover_color="#45a049"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="✏️ Edytuj",
            width=100,
            height=40,
            command=self.edit_selected_product,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="📋 Słownik materiałów",
            width=150,
            height=40,
            command=self.open_materials_dict,
            fg_color="#607D8B"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🔄 Odśwież",
            width=100,
            height=40,
            command=self.load_products,
            fg_color="#757575"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="⚙️ Ustawienia",
            width=110,
            height=40,
            command=self.open_settings,
            fg_color="#9E9E9E",
            hover_color="#757575"
        ).pack(side="left", padx=5)

        # Filters frame with better layout
        filters_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        filters_frame.pack(fill="x", padx=10, pady=5)

        # Search and filters
        search_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Szukaj:", width=60).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=300,
            placeholder_text="Nazwa, indeks lub klient..."
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.apply_filters)

        ctk.CTkLabel(search_frame, text="Materiał:", width=60).pack(side="left", padx=10)
        self.material_filter = ctk.CTkComboBox(
            search_frame,
            width=200,
            values=["Wszystkie"],
            command=lambda e: self.apply_filters()
        )
        self.material_filter.pack(side="left", padx=5)

        ctk.CTkLabel(search_frame, text="Klient:", width=50).pack(side="left", padx=10)
        self.customer_filter = ctk.CTkComboBox(
            search_frame,
            width=200,
            values=["Wszyscy"],
            command=lambda e: self.apply_filters()
        )
        self.customer_filter.pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="❌ Wyczyść filtry",
            width=120,
            command=self.clear_filters,
            fg_color="#666666"
        ).pack(side="right", padx=5)

        # Products table with headers
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Table header
        header_frame = ctk.CTkFrame(table_container, height=40, fg_color="#3c3c3c")
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # Header columns
        headers = [
            ("", 60),  # Thumbnail
            ("Indeks", 120),
            ("Nazwa", 300),
            ("Materiał", 150),
            ("Grubość", 80),
            ("Klient", 200),
            ("Cena", 120),
            ("Utworzono", 100)
        ]

        for header, width in headers:
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                width=width,
                font=ctk.CTkFont(weight="bold"),
                anchor="w" if header else "center"
            )
            label.pack(side="left", padx=5, pady=5)

        # Scrollable frame for products
        self.products_scroll = ctk.CTkScrollableFrame(
            table_container,
            fg_color="#1e1e1e"
        )
        self.products_scroll.pack(fill="both", expand=True)

        # Products container
        self.products_container = ctk.CTkFrame(self.products_scroll, fg_color="transparent")
        self.products_container.pack(fill="both", expand=True)

        # Status bar with better info
        status_container = ctk.CTkFrame(self, height=35, fg_color="#2b2b2b")
        status_container.pack(fill="x")
        status_container.pack_propagate(False)

        self.status_bar = ctk.CTkLabel(
            status_container,
            text="Gotowy",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.status_bar.pack(side="left", padx=10, pady=5)

        self.count_label = ctk.CTkLabel(
            status_container,
            text="",
            anchor="e",
            font=ctk.CTkFont(size=12)
        )
        self.count_label.pack(side="right", padx=10, pady=5)

        # Load filter options
        self.load_filter_options()

    def load_filter_options(self):
        """Load options for filter dropdowns"""
        try:
            # Load materials
            materials_response = self.db.client.table('materials_dict').select("*").eq('is_active', True).order('name').execute()
            material_names = ["Wszystkie"] + [m['name'] for m in materials_response.data]
            self.material_filter.configure(values=material_names)

            # Load customers
            customers_response = self.db.client.table('customers').select("name").order('name').execute()
            customer_names = ["Wszyscy"] + [c['name'] for c in customers_response.data]
            self.customer_filter.configure(values=customer_names)

        except Exception as e:
            print(f"Error loading filter options: {e}")

    def load_products(self):
        """Load products from products_catalog table"""
        try:
            self.status_bar.configure(text="Ładowanie produktów...")

            # Clear thumbnail cache to force reload of updated thumbnails
            self.thumbnail_cache.clear()
            print("DEBUG: Cleared thumbnail cache for refresh")

            # Load from products_catalog with joined data
            response = self.db.client.table('products_catalog').select(
                """
                *,
                materials_dict!material_id(name, category),
                customers!customer_id(name, short_name)
                """
            ).eq('is_active', True).order('created_at', desc=True).execute()

            self.products_data = response.data
            self.filtered_products = self.products_data

            # Debug: check thumbnails and URLs
            products_with_thumbnails = sum(1 for p in self.products_data if p.get('thumbnail_100'))
            products_with_thumbnail_urls = sum(1 for p in self.products_data if p.get('thumbnail_100_url'))
            print(f"DEBUG: Loaded {len(self.products_data)} products")
            print(f"  - {products_with_thumbnails} have thumbnail_100 (old bytea)")
            print(f"  - {products_with_thumbnail_urls} have thumbnail_100_url (new URL)")

            # Debug: check first product's fields
            if self.products_data:
                print(f"\nDEBUG: First product keys: {list(self.products_data[0].keys())}")
                first_product = self.products_data[0]
                print(f"  - cad_2d_url: {first_product.get('cad_2d_url', 'NOT FOUND')}")
                print(f"  - cad_3d_url: {first_product.get('cad_3d_url', 'NOT FOUND')}")
                print(f"  - user_image_url: {first_product.get('user_image_url', 'NOT FOUND')}")
                print(f"  - thumbnail_100_url: {first_product.get('thumbnail_100_url', 'NOT FOUND')}")

            self.display_products(self.filtered_products)
            self.update_status()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować produktów:\n{e}")
            self.status_bar.configure(text="Błąd ładowania")

    def apply_filters(self, event=None):
        """Apply all filters to product list"""
        filtered = []

        # Get filter values
        search_text = self.search_entry.get().lower()
        material_name = self.material_filter.get()
        customer_name = self.customer_filter.get()

        for product in self.products_data:
            # Search filter
            if search_text:
                searchable = [
                    product.get('name', '').lower(),
                    product.get('idx_code', '').lower(),
                    product.get('description', '').lower()
                ]
                if product.get('customers'):
                    searchable.append(product['customers'].get('name', '').lower())

                if not any(search_text in s for s in searchable):
                    continue

            # Material filter
            if material_name != "Wszystkie":
                if not product.get('materials_dict') or product['materials_dict'].get('name') != material_name:
                    continue

            # Customer filter
            if customer_name != "Wszyscy":
                if not product.get('customers') or product['customers'].get('name') != customer_name:
                    continue

            filtered.append(product)

        self.filtered_products = filtered
        self.display_products(self.filtered_products)
        self.update_status()

    def clear_filters(self):
        """Clear all filters"""
        self.search_entry.delete(0, "end")
        self.material_filter.set("Wszystkie")
        self.customer_filter.set("Wszyscy")
        self.apply_filters()

    def display_products(self, products: List[Dict]):
        """Display products with enhanced row formatting"""
        # Clear existing widgets
        for widget in self.products_container.winfo_children():
            widget.destroy()

        self.selected_product = None
        self.selected_row_frame = None

        # Display each product
        for i, product in enumerate(products):
            self.create_enhanced_product_row(product, i)

    def create_enhanced_product_row(self, product: Dict, index: int):
        """Create an enhanced row with proper selection and thumbnails"""
        # Row container with hover effect - height from settings
        row_height = self.settings.get('row_height', 80)

        # Get colors from settings
        even_color = self.settings.get('even_row_color', '#2b2b2b')
        odd_color = self.settings.get('odd_row_color', '#252525')

        row = ctk.CTkFrame(
            self.products_container,
            height=row_height,
            fg_color=even_color if index % 2 == 0 else odd_color,
            corner_radius=0
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Store product reference
        row.product = product

        # Bind events for selection
        def select_row(event=None):
            self.select_product_row(row, product)

        def show_context(event):
            self.select_product_row(row, product)
            self.show_context_menu(event, product)

        row.bind("<Button-1>", select_row)
        row.bind("<Double-Button-1>", lambda e: self.view_product_details(product))
        row.bind("<Button-3>", show_context)

        # Thumbnail - size based on row height setting
        if self.settings.get('show_thumbnails', True):
            thumb_width = int(row_height * 1.25)  # Width proportional to height
            thumb_height = int(row_height * 0.875)  # Slightly smaller than row height

            thumb_frame = ctk.CTkLabel(row, text="", width=thumb_width, height=thumb_height)
            thumb_frame.pack(side="left", padx=8, pady=5)
            thumb_frame.bind("<Button-1>", select_row)
            thumb_frame.bind("<Button-3>", show_context)

            # Load thumbnail if available - check URL first, then fallback to bytea
            if product.get('thumbnail_100_url') or product.get('thumbnail_100'):
                try:
                    # Pass bytea data if available, load_thumbnail will try URL first
                    thumbnail_data = product.get('thumbnail_100')
                    self.load_thumbnail(thumb_frame, thumbnail_data, product['id'], thumb_width, thumb_height)
                except:
                    thumb_frame.configure(text="📦")
            else:
                thumb_frame.configure(text="📦")

        # Index
        self.create_row_label(row, product.get('idx_code', '-'), 120, select_row, show_context)

        # Name
        self.create_row_label(row, product.get('name', '-'), 300, select_row, show_context)

        # Material
        material_text = product.get('materials_dict', {}).get('name', '-') if product.get('materials_dict') else '-'
        self.create_row_label(row, material_text, 150, select_row, show_context)

        # Thickness
        thickness_text = f"{product.get('thickness_mm', '-')} mm" if product.get('thickness_mm') else "-"
        self.create_row_label(row, thickness_text, 80, select_row, show_context)

        # Customer
        customer_text = product.get('customers', {}).get('name', '-') if product.get('customers') else '-'
        self.create_row_label(row, customer_text, 200, select_row, show_context)

        # Total cost
        total_cost = self.calculate_total_cost(product)
        cost_text = f"{total_cost:.2f} PLN" if total_cost > 0 else "-"
        self.create_row_label(row, cost_text, 120, select_row, show_context)

        # Date
        date_text = "-"
        if product.get('created_at'):
            try:
                date_obj = datetime.fromisoformat(product['created_at'].replace('Z', '+00:00'))
                date_text = date_obj.strftime('%Y-%m-%d')
            except:
                pass
        self.create_row_label(row, date_text, 100, select_row, show_context)

    def create_row_label(self, parent, text, width, click_handler, context_handler):
        """Helper to create row labels with consistent styling"""
        font_size = self.settings.get('font_size', 12)
        label = ctk.CTkLabel(
            parent,
            text=text,
            width=width,
            anchor="w",
            font=ctk.CTkFont(size=font_size)
        )
        label.pack(side="left", padx=5)
        label.bind("<Button-1>", click_handler)
        label.bind("<Button-3>", context_handler)
        return label

    def load_thumbnail(self, label, thumbnail_data, product_id, width=90, height=65):
        """Load and display thumbnail image from URL or legacy bytea"""
        cache_key = f"{product_id}_{width}x{height}"
        if cache_key in self.thumbnail_cache:
            label.configure(image=self.thumbnail_cache[cache_key])
            return

        try:
            img_data = None

            # First try to load from URL (new way)
            product = next((p for p in self.products_data if p['id'] == product_id), None)
            if product and product.get('thumbnail_100_url'):
                print(f"DEBUG load_thumbnail: Loading from URL: {product['thumbnail_100_url']}")
                try:
                    import requests
                    response = requests.get(product['thumbnail_100_url'], timeout=5)
                    if response.status_code == 200:
                        img_data = response.content
                        print(f"DEBUG: Downloaded thumbnail {len(img_data)} bytes")
                except Exception as e:
                    print(f"DEBUG: Failed to download thumbnail from URL: {e}")

            # Fallback to legacy bytea if URL not available
            if not img_data and thumbnail_data:
                print(f"DEBUG load_thumbnail: Fallback to bytea data")
                print(f"DEBUG load_thumbnail: data type={type(thumbnail_data).__name__}")
                if isinstance(thumbnail_data, str):
                    print(f"DEBUG load_thumbnail: string length={len(thumbnail_data)}")
                elif isinstance(thumbnail_data, (bytes, bytearray, memoryview)):
                    print(f"DEBUG load_thumbnail: binary length={len(thumbnail_data)}")
                # Use safe_decode_binary function to handle all formats
                img_data = safe_decode_binary(thumbnail_data, "thumbnail_100")

            if not img_data:
                print(f"DEBUG load_thumbnail: safe_decode_binary returned None for product {product_id}")
                label.configure(text="📦")
                return

            print(f"DEBUG load_thumbnail: decoded data length={len(img_data)}")
            print(f"DEBUG load_thumbnail: first 8 bytes={img_data[:8].hex()}")

            # Open image from decoded data
            img = Image.open(io.BytesIO(img_data))
            print(f"DEBUG load_thumbnail: Image opened successfully - size={img.size}, mode={img.mode}")

            # Create CTkImage for proper display with dynamic size
            # CTkImage handles scaling and HiDPI displays better
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))

            # Cache and display with size-specific key
            self.thumbnail_cache[cache_key] = ctk_image
            label.configure(image=ctk_image, text="")
            print(f"DEBUG load_thumbnail: Thumbnail displayed successfully for product {product_id}")

        except Exception as e:
            print(f"ERROR loading thumbnail for product {product_id}: {e}")
            import traceback
            traceback.print_exc()
            label.configure(text="📦")

    def calculate_total_cost(self, product):
        """Calculate total cost for a product"""
        # Używamy material_laser_cost zamiast osobnych material_cost i laser_cost
        material_laser_cost = float(product.get('material_laser_cost', 0) or 0)
        bending_cost = float(product.get('bending_cost', 0) or 0)
        additional_costs = float(product.get('additional_costs', 0) or 0)

        total = material_laser_cost + bending_cost + additional_costs

        # Debug log
        if product.get('name') == 'test10':
            print(f"DEBUG: Calculating cost for {product.get('name')}")
            print(f"  material_laser_cost: {material_laser_cost}")
            print(f"  bending_cost: {bending_cost}")
            print(f"  additional_costs: {additional_costs}")
            print(f"  TOTAL: {total}")

        return total

    def select_product_row(self, row_frame, product):
        """Select a product row with visual feedback"""
        # Deselect previous
        if self.selected_row_frame:
            # Restore original color based on row index
            index = self.products_container.winfo_children().index(self.selected_row_frame)
            even_color = self.settings.get('even_row_color', '#2b2b2b')
            odd_color = self.settings.get('odd_row_color', '#252525')
            original_color = even_color if index % 2 == 0 else odd_color
            self.selected_row_frame.configure(fg_color=original_color)

        # Select new
        self.selected_row_frame = row_frame
        self.selected_product = product
        selected_color = self.settings.get('selected_row_color', '#3a5f8a')
        row_frame.configure(fg_color=selected_color)  # Highlight color

        # Update status
        self.status_bar.configure(
            text=f"Wybrano: {product.get('name')} ({product.get('idx_code')})"
        )

    def update_status(self):
        """Update status bar with counts"""
        total = len(self.products_data)
        filtered = len(self.filtered_products)

        if total == filtered:
            self.count_label.configure(text=f"Produkty: {total}")
        else:
            self.count_label.configure(text=f"Wyświetlono: {filtered} z {total}")

        if filtered == 0:
            self.status_bar.configure(text="Brak produktów do wyświetlenia")
        else:
            self.status_bar.configure(text="Gotowy")

    def view_product_details(self, product: Dict):
        """Show product details using the enhanced edit dialog in view mode"""
        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],
            part_data=product,
            part_index=None,
            order_id=None,
            view_only=True,
            title="Szczegóły produktu"
        )
        self.wait_window(dialog)

    def add_product(self):
        """Add new product to catalog"""
        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],
            part_data=None,
            part_index=None,
            order_id=None,
            catalog_mode=True,  # Indicate we're adding to catalog
            title="Dodaj produkt do katalogu"
        )
        self.wait_window(dialog)

        # Save to products_catalog if data was provided
        if hasattr(dialog, 'part_data') and dialog.part_data:
            self.save_product_to_catalog(dialog.part_data, is_new=True)

            # Auto-refresh if enabled in settings
            if self.settings.get('auto_refresh_on_edit', True):
                print("DEBUG: Auto-refreshing product list after adding new product...")
                self.load_products()

    def edit_selected_product(self):
        """Edit the selected product"""
        if not self.selected_product:
            messagebox.showwarning("Uwaga", "Wybierz produkt do edycji")
            return

        self.edit_product(self.selected_product)

    def edit_product(self, product: Dict):
        """Edit product in catalog"""
        print("\n" + "="*50)
        print("DEBUG: edit_product START")
        print(f"DEBUG: product id={product.get('id')}")
        print(f"DEBUG: product keys: {list(product.keys())}")
        print("\nDEBUG: Product URL fields:")
        print(f"  - cad_2d_url: {product.get('cad_2d_url', 'NOT FOUND')}")
        print(f"  - cad_3d_url: {product.get('cad_3d_url', 'NOT FOUND')}")
        print(f"  - user_image_url: {product.get('user_image_url', 'NOT FOUND')}")
        print(f"  - thumbnail_100_url: {product.get('thumbnail_100_url', 'NOT FOUND')}")
        print(f"  - preview_800_url: {product.get('preview_800_url', 'NOT FOUND')}")
        print(f"  - preview_4k_url: {product.get('preview_4k_url', 'NOT FOUND')}")
        print("="*50 + "\n")

        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],
            part_data=product,
            part_index=None,
            order_id=None,
            catalog_mode=True,
            title="Edytuj produkt"
        )
        self.wait_window(dialog)

        # Update product if changes were made
        if hasattr(dialog, 'part_data') and dialog.part_data:
            print(f"DEBUG: Dialog returned data, saving to catalog...")
            print(f"DEBUG: Product ID from original product: {product.get('id')} (type: {type(product.get('id')).__name__})")
            print(f"DEBUG: Dialog part_data keys: {list(dialog.part_data.keys()) if dialog.part_data else 'None'}")
            self.save_product_to_catalog(dialog.part_data, is_new=False, product_id=product['id'])

            # Auto-refresh if enabled in settings
            if self.settings.get('auto_refresh_on_edit', True):
                print("DEBUG: Auto-refreshing product list after edit...")
                self.load_products()
        else:
            print(f"DEBUG: Dialog cancelled or no data returned")

    def load_settings(self):
        """Load settings from file or return defaults"""
        import json
        import os

        settings_file = os.path.join(os.path.expanduser("~"), ".mfg_products_settings.json")

        default_settings = {
            'row_height': 80,
            'show_thumbnails': True,
            'even_row_color': '#2b2b2b',
            'odd_row_color': '#252525',
            'selected_row_color': '#3a5f8a',
            'font_size': 12,
            'auto_refresh_on_edit': True
        }

        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")

        return default_settings

    def save_settings_to_file(self):
        """Save current settings to file"""
        import json
        import os

        settings_file = os.path.join(os.path.expanduser("~"), ".mfg_products_settings.json")

        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"Settings saved to {settings_file}")
        except Exception as e:
            print(f"Error saving settings: {e}")
            messagebox.showerror("Błąd", f"Nie można zapisać ustawień: {e}")

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.settings)
        self.wait_window(dialog)

        if dialog.result:
            # Apply new settings
            self.settings = dialog.result
            self.save_settings_to_file()

            # Reload product list with new settings
            self.display_products(self.filtered_products)

            messagebox.showinfo("Ustawienia", "Ustawienia zostały zapisane i zastosowane.")

    def save_product_to_catalog(self, part_data: Dict, is_new: bool = True, product_id: str = None):
        """Save product to products_catalog table with binary file storage"""
        try:
            # Write debug to file
            import json
            from datetime import datetime

            debug_log = []
            debug_log.append(f"\n{'='*60}")
            debug_log.append(f"DEBUG LOG: {datetime.now().isoformat()}")
            debug_log.append(f"{'='*60}")
            debug_log.append(f"save_product_to_catalog START")
            debug_log.append(f"is_new={is_new}, product_id={product_id}")
            debug_log.append(f"part_data keys: {list(part_data.keys())}")

            # Write to debug file
            with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                for line in debug_log:
                    f.write(line + '\n')
                    print(f"DEBUG: {line}")

            print("\n" + "="*50)
            print("DEBUG: save_product_to_catalog START")
            print(f"DEBUG: is_new={is_new}, product_id={product_id}")
            print(f"DEBUG: part_data keys: {list(part_data.keys())}")
            print("="*50 + "\n")

            # Prepare data for database
            db_data = {
                'name': part_data['name'],
                'material_id': part_data.get('material_id'),
                'thickness_mm': part_data.get('thickness_mm'),
                'customer_id': part_data.get('customer_id'),
                'bending_cost': part_data.get('bending_cost', 0),
                'additional_costs': part_data.get('additional_costs', 0),
                'material_laser_cost': part_data.get('material_laser_cost', 0),
                'material_cost': part_data.get('material_cost', 0),
                'laser_cost': part_data.get('laser_cost', 0),
                'description': part_data.get('description', ''),
                'notes': part_data.get('notes', ''),
                'category': part_data.get('category'),
                'is_active': True
            }

            # Add physical product parameters (if provided)
            if part_data.get('width_mm') is not None:
                db_data['width_mm'] = part_data['width_mm']
            if part_data.get('height_mm') is not None:
                db_data['height_mm'] = part_data['height_mm']
            if part_data.get('length_mm') is not None:
                db_data['length_mm'] = part_data['length_mm']
            if part_data.get('weight_kg') is not None:
                db_data['weight_kg'] = part_data['weight_kg']
            if part_data.get('surface_area_m2') is not None:
                db_data['surface_area_m2'] = part_data['surface_area_m2']
            if part_data.get('production_time_minutes') is not None:
                db_data['production_time_minutes'] = part_data['production_time_minutes']
            if part_data.get('machine_type'):
                db_data['machine_type'] = part_data['machine_type']

            # Add audit fields
            try:
                current_user = getpass.getuser()
            except Exception:
                current_user = "unknown"

            if is_new:
                db_data['created_by'] = current_user
            db_data['updated_by'] = current_user

            print(f"DEBUG: Basic db_data prepared with {len(db_data)} fields")

            # Write basic data to log
            with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"Basic db_data fields:\n")
                for key, value in db_data.items():
                    value_info = f"type={type(value).__name__}, value={value}" if value is not None else "None"
                    f.write(f"  {key}: {value_info}\n")

            # Store file metadata ONLY (not binary data - that goes to Storage)
            # We keep the metadata for file info display
            if part_data.get('cad_2d_binary'):
                if isinstance(part_data['cad_2d_binary'], bytes):
                    db_data['cad_2d_filesize'] = len(part_data['cad_2d_binary'])
                db_data['cad_2d_filename'] = part_data.get('cad_2d_filename')

            if part_data.get('cad_3d_binary'):
                if isinstance(part_data['cad_3d_binary'], bytes):
                    db_data['cad_3d_filesize'] = len(part_data['cad_3d_binary'])
                db_data['cad_3d_filename'] = part_data.get('cad_3d_filename')

            if part_data.get('user_image_binary'):
                if isinstance(part_data['user_image_binary'], bytes):
                    db_data['user_image_filesize'] = len(part_data['user_image_binary'])
                db_data['user_image_filename'] = part_data.get('user_image_filename')

            # Additional documentation metadata
            if part_data.get('additional_documentation'):
                if isinstance(part_data['additional_documentation'], bytes):
                    db_data['additional_documentation_filesize'] = len(part_data['additional_documentation'])
                db_data['additional_documentation_filename'] = part_data.get('additional_documentation_filename')

            # Primary graphic source
            if part_data.get('primary_graphic_source'):
                db_data['primary_graphic_source'] = part_data['primary_graphic_source']

            # Generate thumbnails based on primary_graphic_source selection
            thumbnails_generated = False
            image_source = None
            source_type = part_data.get('primary_graphic_source', '')

            print(f"DEBUG: primary_graphic_source = '{source_type}'")

            # Wybierz źródło miniatur na podstawie ustawienia "użyj jako główną grafikę"
            if source_type == 'USER' and part_data.get('user_image_binary'):
                # Użytkownik wybrał "Grafika" jako główne źródło
                if isinstance(part_data['user_image_binary'], bytes):
                    image_source = part_data['user_image_binary']
                    print(f"DEBUG: Using USER image (grafika użytkownika) for thumbnails")

            elif source_type == '2D' and part_data.get('cad_2d_binary'):
                # Użytkownik wybrał "2D" jako główne źródło
                print(f"DEBUG: 2D selected as primary source")
                if isinstance(part_data['cad_2d_binary'], bytes):
                    # Konwertuj CAD 2D do obrazu
                    filename = part_data.get('cad_2d_filename', 'file.dxf')
                    print(f"DEBUG: Converting CAD 2D file '{filename}' to image...")
                    # Zapisz tymczasowo do pliku dla ThumbnailGenerator
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
                        tmp.write(part_data['cad_2d_binary'])
                        tmp_path = tmp.name
                    try:
                        # Użyj ThumbnailGenerator który ma prawdziwą implementację
                        image_source = ThumbnailGenerator.generate_from_2d_cad(tmp_path, (800, 800))
                        if image_source:
                            print(f"DEBUG: CAD 2D successfully converted to image")
                        else:
                            print(f"DEBUG: CAD 2D conversion failed")
                    finally:
                        import os
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

            elif source_type == '3D' and part_data.get('cad_3d_binary'):
                # Użytkownik wybrał "3D" jako główne źródło
                print(f"DEBUG: 3D selected as primary source")
                if isinstance(part_data['cad_3d_binary'], bytes):
                    # Renderuj CAD 3D do obrazu
                    filename = part_data.get('cad_3d_filename', 'file.step')
                    print(f"DEBUG: Rendering CAD 3D file '{filename}' to image...")
                    # Zapisz tymczasowo do pliku dla ThumbnailGenerator
                    import tempfile
                    import os
                    ext = os.path.splitext(filename)[1] or '.step'
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                        tmp.write(part_data['cad_3d_binary'])
                        tmp_path = tmp.name
                    try:
                        # Użyj ThumbnailGenerator który ma prawdziwą implementację z VTK
                        image_source = ThumbnailGenerator.generate_from_3d_cad(tmp_path, (800, 800))
                        if image_source:
                            print(f"DEBUG: CAD 3D successfully rendered to image")
                        else:
                            print(f"DEBUG: CAD 3D rendering failed")
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

            else:
                # Jeśli nie ma ustawionego primary_graphic_source, próbuj znaleźć jakiekolwiek źródło
                print(f"DEBUG: No primary_graphic_source set or no data for selected source")
                if part_data.get('user_image_binary'):
                    if isinstance(part_data['user_image_binary'], bytes):
                        image_source = part_data['user_image_binary']
                        print(f"DEBUG: Fallback - using user_image_binary for thumbnails")

            # Generate thumbnails from image source
            if image_source:
                print(f"DEBUG: Generating thumbnails from image source...")
                thumbnails = generate_thumbnails_from_image(image_source)
                if thumbnails:
                    # Override any existing thumbnail data with newly generated
                    part_data['thumbnail_100'] = thumbnails.get('thumbnail_100')
                    part_data['preview_800'] = thumbnails.get('preview_800')
                    part_data['preview_4k'] = thumbnails.get('preview_4k')
                    thumbnails_generated = True
                    print(f"DEBUG: Thumbnails generated successfully")

            # Don't store thumbnail binary data - they will be uploaded to Storage
            # The URLs will be added after successful upload

            print(f"DEBUG: Final db_data has {len(db_data)} fields")
            print(f"DEBUG: db_data keys: {list(db_data.keys())}")

            # Check for any problematic fields
            print(f"DEBUG: Checking db_data fields for potential issues...")
            for key, value in db_data.items():
                if value is not None:
                    value_type = type(value).__name__
                    if isinstance(value, (str, bytes)):
                        value_len = len(value)
                        # Show preview for short values, length for long ones
                        if value_len < 100 and not key.endswith('_binary'):
                            print(f"DEBUG: Field '{key}': type={value_type}, value='{value}'")
                        else:
                            print(f"DEBUG: Field '{key}': type={value_type}, length={value_len}")
                    else:
                        print(f"DEBUG: Field '{key}': type={value_type}, value={value}")
                else:
                    print(f"DEBUG: Field '{key}': value=None")

            # ============================================
            # UPLOAD FILES TO SUPABASE STORAGE
            # ============================================
            print(f"DEBUG: Starting file uploads to Supabase Storage...")

            # Determine product_id for storage path
            storage_product_id = product_id if not is_new else str(uuid.uuid4())
            if is_new:
                print(f"DEBUG: Generated new product_id for storage: {storage_product_id}")

            # Track uploaded URLs
            uploaded_urls = {}

            # Upload CAD 2D file
            if part_data.get('cad_2d_binary') and isinstance(part_data['cad_2d_binary'], bytes):
                print(f"DEBUG: Uploading CAD 2D file to Storage...")
                filename = part_data.get('cad_2d_filename', 'cad_2d.dxf')
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'cad_2d',
                    part_data['cad_2d_binary'], filename
                )
                if success:
                    uploaded_urls['cad_2d_url'] = result
                    db_data['cad_2d_url'] = result
                    print(f"DEBUG: CAD 2D uploaded successfully: {result}")
                else:
                    print(f"DEBUG: CAD 2D upload failed: {result}")

            # Upload CAD 3D file
            if part_data.get('cad_3d_binary') and isinstance(part_data['cad_3d_binary'], bytes):
                print(f"DEBUG: Uploading CAD 3D file to Storage...")
                filename = part_data.get('cad_3d_filename', 'cad_3d.step')
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'cad_3d',
                    part_data['cad_3d_binary'], filename
                )
                if success:
                    uploaded_urls['cad_3d_url'] = result
                    db_data['cad_3d_url'] = result
                    print(f"DEBUG: CAD 3D uploaded successfully: {result}")
                else:
                    print(f"DEBUG: CAD 3D upload failed: {result}")

            # Upload user image
            if part_data.get('user_image_binary') and isinstance(part_data['user_image_binary'], bytes):
                print(f"DEBUG: Uploading user image to Storage...")
                filename = part_data.get('user_image_filename', 'image.png')
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'user_image',
                    part_data['user_image_binary'], filename
                )
                if success:
                    uploaded_urls['user_image_url'] = result
                    db_data['user_image_url'] = result
                    print(f"DEBUG: User image uploaded successfully: {result}")
                else:
                    print(f"DEBUG: User image upload failed: {result}")

            # Upload documentation
            if part_data.get('additional_documentation') and isinstance(part_data['additional_documentation'], bytes):
                print(f"DEBUG: Uploading documentation to Storage...")
                filename = part_data.get('additional_documentation_filename', 'docs.zip')
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'documentation',
                    part_data['additional_documentation'], filename
                )
                if success:
                    uploaded_urls['additional_documentation_url'] = result
                    db_data['additional_documentation_url'] = result
                    print(f"DEBUG: Documentation uploaded successfully: {result}")
                else:
                    print(f"DEBUG: Documentation upload failed: {result}")

            # Upload thumbnails
            if part_data.get('thumbnail_100') and isinstance(part_data['thumbnail_100'], bytes):
                print(f"DEBUG: Uploading thumbnail_100 to Storage...")
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'thumbnail_100',
                    part_data['thumbnail_100'], 'thumbnail_100.png'
                )
                if success:
                    uploaded_urls['thumbnail_100_url'] = result
                    db_data['thumbnail_100_url'] = result
                    print(f"DEBUG: Thumbnail 100 uploaded successfully: {result}")
                else:
                    print(f"DEBUG: Thumbnail 100 upload failed: {result}")

            if part_data.get('preview_800') and isinstance(part_data['preview_800'], bytes):
                print(f"DEBUG: Uploading preview_800 to Storage...")
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'preview_800',
                    part_data['preview_800'], 'preview_800.png'
                )
                if success:
                    uploaded_urls['preview_800_url'] = result
                    db_data['preview_800_url'] = result
                    print(f"DEBUG: Preview 800 uploaded successfully: {result}")
                else:
                    print(f"DEBUG: Preview 800 upload failed: {result}")

            if part_data.get('preview_4k') and isinstance(part_data['preview_4k'], bytes):
                print(f"DEBUG: Uploading preview_4k to Storage...")
                success, result = upload_product_file(
                    self.db.client, storage_product_id, 'preview_4k',
                    part_data['preview_4k'], 'preview_4k.png'
                )
                if success:
                    uploaded_urls['preview_4k_url'] = result
                    db_data['preview_4k_url'] = result
                    print(f"DEBUG: Preview 4K uploaded successfully: {result}")
                else:
                    print(f"DEBUG: Preview 4K upload failed: {result}")

            print(f"DEBUG: Uploaded {len(uploaded_urls)} files to Storage")
            print(f"DEBUG: URL fields added to db_data: {list(uploaded_urls.keys())}")

            # ============================================
            # END OF STORAGE UPLOADS
            # ============================================

            # Save to database
            if is_new:
                print(f"DEBUG: Inserting NEW product to database...")
                print(f"DEBUG: Sending data with keys: {list(db_data.keys())}")
                response = self.db.client.table('products_catalog').insert(db_data).execute()
                print(f"DEBUG: Insert response: {response}")
                messagebox.showinfo("Sukces", "Produkt został dodany do katalogu")
            else:
                print(f"DEBUG: Updating EXISTING product id={product_id}")

                # Check if product_id is valid
                if product_id is None:
                    raise ValueError("Product ID is None - cannot update without valid ID")

                print(f"DEBUG: Product ID type: {type(product_id).__name__}")
                print(f"DEBUG: Sending data with keys: {list(db_data.keys())}")

                # Ensure product_id is an integer if it's a string
                if isinstance(product_id, str):
                    try:
                        product_id = int(product_id)
                        print(f"DEBUG: Converted product_id to int: {product_id}")
                    except ValueError:
                        print(f"DEBUG: Could not convert product_id to int, keeping as string: {product_id}")

                # Log the actual update call
                print(f"DEBUG: Calling update with db_data keys: {sorted(db_data.keys())}")
                print(f"DEBUG: Using product_id={product_id} (type: {type(product_id).__name__})")

                # Write update details to log
                with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"\nATTEMPTING UPDATE:\n")
                    f.write(f"Product ID: {product_id} (type: {type(product_id).__name__})\n")
                    f.write(f"Fields being sent: {sorted(db_data.keys())}\n")
                    f.write(f"Full update data:\n")
                    for key, value in sorted(db_data.items()):
                        if value is not None:
                            if isinstance(value, str) and len(value) > 100:
                                f.write(f"  {key}: [STRING, length={len(value)}]\n")
                            else:
                                f.write(f"  {key}: {value}\n")
                        else:
                            f.write(f"  {key}: None\n")

                try:
                    # First, try to update with all fields
                    response = self.db.client.table('products_catalog').update(db_data).eq('id', product_id).execute()
                    print(f"DEBUG: Update response successful")
                    print(f"DEBUG: Response data: {response.data if hasattr(response, 'data') else 'No data'}")

                    # Log success
                    with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                        f.write(f"\nUPDATE SUCCESS!\n")
                        f.write(f"Response: {response}\n")

                except Exception as update_error:
                    print(f"DEBUG: Update error details: {update_error}")
                    print(f"DEBUG: Error type: {type(update_error).__name__}")

                    # Log error details
                    with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                        f.write(f"\nUPDATE ERROR!\n")
                        f.write(f"Error type: {type(update_error).__name__}\n")
                        f.write(f"Error message: {str(update_error)}\n")
                        if hasattr(update_error, '__dict__'):
                            f.write(f"Error attributes: {update_error.__dict__}\n")

                    # Try to get more details about the error
                    if hasattr(update_error, '__dict__'):
                        print(f"DEBUG: Error attributes: {update_error.__dict__}")

                    # Try alternative update without binary fields
                    print("\nDEBUG: Trying alternative update without binary fields...")
                    # Exclude binary fields and potentially problematic metadata fields
                    basic_data = {k: v for k, v in db_data.items()
                                 if not k.endswith('_binary')
                                 and not k.endswith('_filesize')
                                 and not k.endswith('_filename')
                                 and not k.startswith('thumbnail_')
                                 and not k.startswith('preview_')
                                 and k != 'primary_graphic_source'}  # Also exclude this potentially missing field

                    print(f"DEBUG: Basic data keys: {list(basic_data.keys())}")

                    # Log attempt
                    with open('product_update_debug.log', 'a', encoding='utf-8') as f:
                        f.write(f"\nTRYING ALTERNATIVE UPDATE (basic fields only):\n")
                        f.write(f"Fields: {list(basic_data.keys())}\n")

                    try:
                        response = self.db.client.table('products_catalog').update(basic_data).eq('id', product_id).execute()
                        print(f"DEBUG: Alternative update successful (without binary fields)")

                        # Now try to update file-related fields separately
                        # First, handle binary data fields
                        binary_fields = {k: v for k, v in db_data.items()
                                       if k.endswith('_binary') or k.startswith('thumbnail_')
                                       or k.startswith('preview_')}

                        if binary_fields:
                            print(f"DEBUG: Updating binary fields separately: {list(binary_fields.keys())}")
                            try:
                                self.db.client.table('products_catalog').update(binary_fields).eq('id', product_id).execute()
                                print(f"DEBUG: Binary fields update successful")
                            except Exception as bin_error:
                                print(f"DEBUG: Binary fields update failed: {bin_error}")
                                # Continue anyway, at least basic data was updated

                        # Then, handle file metadata fields
                        file_metadata_fields = {k: v for k, v in db_data.items()
                                               if k.endswith('_filesize') or k.endswith('_filename')}

                        if file_metadata_fields:
                            print(f"DEBUG: Updating file metadata separately: {list(file_metadata_fields.keys())}")
                            try:
                                self.db.client.table('products_catalog').update(file_metadata_fields).eq('id', product_id).execute()
                                print(f"DEBUG: File metadata update successful")
                            except Exception as meta_error:
                                print(f"DEBUG: File metadata update failed (might not exist in DB): {meta_error}")
                                # Continue anyway, these fields might not exist in DB

                    except Exception as alt_error:
                        print(f"DEBUG: Alternative update also failed: {alt_error}")
                        raise update_error

                messagebox.showinfo("Sukces", "Produkt został zaktualizowany")

            # Reload products
            self.load_products()

        except Exception as e:
            print(f"\nDEBUG: ERROR in save_product_to_catalog")
            print(f"DEBUG: Error message: {e}")
            print(f"DEBUG: Error type: {type(e).__name__}")

            import traceback
            print("DEBUG: Full traceback:")
            traceback.print_exc()

            messagebox.showerror("Błąd", f"Nie można zapisać produktu:\n{e}")

    def duplicate_product(self, product: Dict):
        """Duplicate selected product"""
        try:
            # Create copy of product
            new_product = product.copy()
            new_product.pop('id', None)
            new_product.pop('idx_code', None)
            new_product['name'] = f"{product['name']} - kopia"
            new_product.pop('created_at', None)
            new_product.pop('updated_at', None)

            # Remove joined data
            new_product.pop('materials_dict', None)
            new_product.pop('customers', None)

            # Save to database
            response = self.db.client.table('products_catalog').insert(new_product).execute()

            messagebox.showinfo("Sukces", "Produkt został zduplikowany")
            self.load_products()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zduplikować produktu:\n{e}")

    def delete_product(self, product: Dict):
        """Delete selected product"""
        result = messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć produkt:\n{product.get('name')}?\n\nUwaga: Produkt zostanie oznaczony jako nieaktywny."
        )

        if result:
            try:
                # Soft delete - mark as inactive
                self.db.client.table('products_catalog').update(
                    {'is_active': False}
                ).eq('id', product['id']).execute()

                messagebox.showinfo("Sukces", "Produkt został usunięty")
                self.load_products()

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można usunąć produktu:\n{e}")

    def show_context_menu(self, event, product: Dict):
        """Show context menu for product row"""
        # Create context menu
        menu = Menu(self, tearoff=0)
        menu.configure(bg="#3c3c3c", fg="white", activebackground="#4a4a4a")

        menu.add_command(label="🔍 Szczegóły", command=lambda: self.view_product_details(product))
        menu.add_command(label="✏️ Edytuj", command=lambda: self.edit_product(product))
        menu.add_command(label="📋 Duplikuj", command=lambda: self.duplicate_product(product))
        menu.add_separator()
        menu.add_command(label="🗑️ Usuń", command=lambda: self.delete_product(product))

        # Show menu
        menu.post(event.x_root, event.y_root)

    def open_materials_dict(self):
        """Open materials dictionary"""
        dialog = MaterialsDictDialog(self, self.db)
        self.wait_window(dialog)
        # Reload filter options after materials might have changed
        self.load_filter_options()