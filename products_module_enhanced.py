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
from PIL import Image, ImageTk
import io
import base64
from pathlib import Path

from image_processing import ImageProcessor, get_cached_image
from materials_dict_module import MaterialsDictDialog
from part_edit_enhanced import EnhancedPartEditDialog


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

def safe_decode_binary(data, field_name="data"):
    """Safely decode binary data from various formats

    Handles double encoding (hex->base64->binary) from Supabase

    Args:
        data: Can be bytes, bytearray, memoryview, hex string, or base64 string
        field_name: Name of the field for error messages

    Returns:
        bytes: The binary data or None if decoding failed
    """
    if not data:
        return None

    try:
        # If it's already bytes, return as is
        if isinstance(data, bytes):
            return data

        # If it's a bytearray or memoryview (from PostgreSQL bytea), convert to bytes
        if isinstance(data, (bytearray, memoryview)):
            return bytes(data)

        # If it's a string, determine format and decode
        if isinstance(data, str):
            # STEP 1: Handle hex encoding (Supabase returns bytea as hex with \x prefix)
            decoded_data = data
            if data.startswith('\\x'):
                # Remove the \x prefix and convert from hex
                hex_str = data[2:]  # Remove '\x' prefix
                decoded_data = bytes.fromhex(hex_str)

                # STEP 2: Check if the result is base64 encoded
                # (Our data is double-encoded: binary -> base64 -> hex)
                try:
                    # Check if decoded hex looks like base64 (all printable ASCII)
                    if all(32 <= b < 127 for b in decoded_data[:min(100, len(decoded_data))]):
                        decoded_str = decoded_data.decode('ascii')

                        # Try base64 decode
                        import re
                        if re.match(r'^[A-Za-z0-9+/\r\n]+=*$', decoded_str[:1000]):  # Check first 1000 chars
                            fixed_base64 = fix_base64_padding(decoded_str)
                            result = base64.b64decode(fixed_base64)
                            return result
                except Exception:
                    pass

                # If not base64, return the hex-decoded data
                return decoded_data

            # Otherwise try base64
            try:
                # Try to fix padding and decode as base64
                fixed_base64 = fix_base64_padding(data)
                return base64.b64decode(fixed_base64)
            except Exception:
                # If base64 fails, try as plain hex string
                try:
                    return bytes.fromhex(data)
                except Exception:
                    return None

    except Exception as e:
        print(f"Warning: Could not decode {field_name}: {str(e)}")
        return None

    return None


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
        # Row container with hover effect
        row = ctk.CTkFrame(
            self.products_container,
            height=50,
            fg_color="#2b2b2b" if index % 2 == 0 else "#252525",
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

        # Thumbnail
        thumb_frame = ctk.CTkLabel(row, text="", width=60, height=40)
        thumb_frame.pack(side="left", padx=5, pady=5)
        thumb_frame.bind("<Button-1>", select_row)
        thumb_frame.bind("<Button-3>", show_context)

        # Load thumbnail if available
        if product.get('thumbnail_100'):
            try:
                self.load_thumbnail(thumb_frame, product['thumbnail_100'], product['id'])
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
        label = ctk.CTkLabel(
            parent,
            text=text,
            width=width,
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        label.pack(side="left", padx=5)
        label.bind("<Button-1>", click_handler)
        label.bind("<Button-3>", context_handler)
        return label

    def load_thumbnail(self, label, thumbnail_data, product_id):
        """Load and display thumbnail image"""
        if product_id in self.thumbnail_cache:
            label.configure(image=self.thumbnail_cache[product_id])
            return

        try:
            if isinstance(thumbnail_data, (bytes, bytearray)):
                img = Image.open(io.BytesIO(thumbnail_data))
            elif isinstance(thumbnail_data, str):
                # Try to decode from base64 first
                try:
                    fixed_base64 = fix_base64_padding(thumbnail_data)
                    img_data = base64.b64decode(fixed_base64)
                    img = Image.open(io.BytesIO(img_data))
                except:
                    # Handle hex string from database
                    if thumbnail_data.startswith('\\x'):
                        hex_str = thumbnail_data.replace('\\x', '')
                        img_data = bytes.fromhex(hex_str)
                        img = Image.open(io.BytesIO(img_data))
                    else:
                        return
            else:
                return

            # Resize to fit
            img.thumbnail((50, 35), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Cache and display
            self.thumbnail_cache[product_id] = photo
            label.configure(image=photo)
            label.image = photo  # Keep reference

        except Exception as e:
            print(f"Error loading thumbnail: {e}")

    def calculate_total_cost(self, product):
        """Calculate total cost for a product"""
        material_cost = float(product.get('material_cost', 0) or 0)
        laser_cost = float(product.get('laser_cost', 0) or 0)
        bending_cost = float(product.get('bending_cost', 0) or 0)
        additional_costs = float(product.get('additional_costs', 0) or 0)

        return material_cost + laser_cost + bending_cost + additional_costs

    def select_product_row(self, row_frame, product):
        """Select a product row with visual feedback"""
        # Deselect previous
        if self.selected_row_frame:
            # Restore original color based on row index
            index = self.products_container.winfo_children().index(self.selected_row_frame)
            original_color = "#2b2b2b" if index % 2 == 0 else "#252525"
            self.selected_row_frame.configure(fg_color=original_color)

        # Select new
        self.selected_row_frame = row_frame
        self.selected_product = product
        row_frame.configure(fg_color="#3a5f8a")  # Highlight color

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

    def edit_selected_product(self):
        """Edit the selected product"""
        if not self.selected_product:
            messagebox.showwarning("Uwaga", "Wybierz produkt do edycji")
            return

        self.edit_product(self.selected_product)

    def edit_product(self, product: Dict):
        """Edit product in catalog"""
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
            self.save_product_to_catalog(dialog.part_data, is_new=False, product_id=product['id'])

    def save_product_to_catalog(self, part_data: Dict, is_new: bool = True, product_id: str = None):
        """Save product to products_catalog table with binary file storage"""
        try:
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

            # Handle binary file storage - encode to base64 for JSON transport
            # IMPORTANT: Supabase REST API requires base64 encoding for JSON serialization,
            # but PostgreSQL automatically decodes it and stores as bytea type.
            # When reading, the data comes back as bytes/bytearray from the bytea column.
            if part_data.get('cad_2d_binary'):
                if isinstance(part_data['cad_2d_binary'], bytes):
                    # Encode bytes to base64 for JSON serialization
                    db_data['cad_2d_binary'] = base64.b64encode(part_data['cad_2d_binary']).decode('utf-8')
                    db_data['cad_2d_filesize'] = len(part_data['cad_2d_binary'])
                else:
                    db_data['cad_2d_binary'] = part_data['cad_2d_binary']
                db_data['cad_2d_filename'] = part_data.get('cad_2d_filename')

            if part_data.get('cad_3d_binary'):
                if isinstance(part_data['cad_3d_binary'], bytes):
                    db_data['cad_3d_binary'] = base64.b64encode(part_data['cad_3d_binary']).decode('utf-8')
                    db_data['cad_3d_filesize'] = len(part_data['cad_3d_binary'])
                else:
                    db_data['cad_3d_binary'] = part_data['cad_3d_binary']
                db_data['cad_3d_filename'] = part_data.get('cad_3d_filename')

            if part_data.get('user_image_binary'):
                if isinstance(part_data['user_image_binary'], bytes):
                    db_data['user_image_binary'] = base64.b64encode(part_data['user_image_binary']).decode('utf-8')
                    db_data['user_image_filesize'] = len(part_data['user_image_binary'])
                else:
                    db_data['user_image_binary'] = part_data['user_image_binary']
                db_data['user_image_filename'] = part_data.get('user_image_filename')

            # Additional documentation
            if part_data.get('additional_documentation'):
                if isinstance(part_data['additional_documentation'], bytes):
                    db_data['additional_documentation'] = base64.b64encode(part_data['additional_documentation']).decode('utf-8')
                    db_data['additional_documentation_filesize'] = len(part_data['additional_documentation'])
                else:
                    db_data['additional_documentation'] = part_data['additional_documentation']
                db_data['additional_documentation_filename'] = part_data.get('additional_documentation_filename')

            # Primary graphic source
            if part_data.get('primary_graphic_source'):
                db_data['primary_graphic_source'] = part_data['primary_graphic_source']

            # Store thumbnails if available - encode to base64 for JSON
            if part_data.get('thumbnail_100'):
                if isinstance(part_data['thumbnail_100'], bytes):
                    db_data['thumbnail_100'] = base64.b64encode(part_data['thumbnail_100']).decode('utf-8')
                else:
                    db_data['thumbnail_100'] = part_data['thumbnail_100']

            if part_data.get('preview_800'):
                if isinstance(part_data['preview_800'], bytes):
                    db_data['preview_800'] = base64.b64encode(part_data['preview_800']).decode('utf-8')
                else:
                    db_data['preview_800'] = part_data['preview_800']

            if part_data.get('preview_4k'):
                if isinstance(part_data['preview_4k'], bytes):
                    db_data['preview_4k'] = base64.b64encode(part_data['preview_4k']).decode('utf-8')
                else:
                    db_data['preview_4k'] = part_data['preview_4k']

            # Save to database
            if is_new:
                response = self.db.client.table('products_catalog').insert(db_data).execute()
                messagebox.showinfo("Sukces", "Produkt został dodany do katalogu")
            else:
                response = self.db.client.table('products_catalog').update(db_data).eq('id', product_id).execute()
                messagebox.showinfo("Sukces", "Produkt został zaktualizowany")

            # Reload products
            self.load_products()

        except Exception as e:
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