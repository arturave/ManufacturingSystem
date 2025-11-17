#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Product Selector Dialog for Orders/Quotes
Version 2.0 with advanced filtering and inline editing
"""

import customtkinter as ctk
from tkinter import messagebox, Menu
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64

from image_processing import ImageProcessor, get_cached_image
from part_edit_enhanced_v4 import EnhancedPartEditDialogV4

# Import thumbnail loader
from thumbnail_loader import get_thumbnail_loader


def fix_base64_padding(data: str) -> str:
    """Fix base64 string padding if needed"""
    if not data:
        return data

    data = data.strip()
    padding_needed = len(data) % 4
    if padding_needed:
        data += '=' * (4 - padding_needed)

    return data


class EditableTreeview(ttk.Treeview):
    """Treeview with inline editing capabilities"""

    def __init__(self, parent, columns, editable_columns=None, on_edit_complete=None, **kwargs):
        super().__init__(parent, columns=columns, **kwargs)
        self.editable_columns = editable_columns or []
        self.on_edit_complete = on_edit_complete
        self._setup_editing()

    def _setup_editing(self):
        """Setup double-click editing"""
        self.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        """Handle double-click for editing"""
        region = self.identify("region", event.x, event.y)
        if region == "cell":
            column = self.identify_column(event.x)
            item = self.identify_row(event.y)

            if not item:
                return

            # Get column index
            col_idx = int(column.replace("#", "")) - 1

            # Check if column is editable
            if col_idx >= len(self['columns']):
                return

            col_name = self['columns'][col_idx]
            if col_name not in self.editable_columns:
                return

            # Get current value
            values = self.item(item, 'values')
            if col_idx >= len(values):
                return

            current_value = values[col_idx]

            # Create entry widget for editing
            x, y, width, height = self.bbox(item, column)

            # Create entry frame
            edit_frame = tk.Frame(self.master, borderwidth=1, relief="solid")
            edit_frame.place(x=x, y=y, width=width, height=height)

            entry = tk.Entry(edit_frame, font=("Segoe UI", 10))
            entry.insert(0, current_value)
            entry.select_range(0, tk.END)
            entry.focus()
            entry.pack(fill="both", expand=True)

            def save_edit(event=None):
                new_value = entry.get()
                if new_value != current_value:
                    # Update treeview
                    values = list(self.item(item, 'values'))
                    values[col_idx] = new_value
                    self.item(item, values=values)

                    # Call callback if provided
                    if self.on_edit_complete:
                        self.on_edit_complete(item, col_name, new_value)

                edit_frame.destroy()

            def cancel_edit(event=None):
                edit_frame.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<Escape>", cancel_edit)
            entry.bind("<FocusOut>", save_edit)


class EnhancedProductSelectorDialog(ctk.CTkToplevel):
    """Enhanced Product Selector with filtering and inline editing"""

    def __init__(self, parent, db, existing_parts: List[Dict] = None, callback: Callable = None):
        super().__init__(parent)
        self.db = db
        self.existing_parts = existing_parts or []
        self.callback = callback

        # Data storage
        self.all_products = []
        self.filtered_products = []
        self.selected_products = []

        # Setup window
        self.title("Wybór Produktów z Katalogu")

        # Make fullscreen
        self.state('zoomed')

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Setup UI
        self._setup_ui()

        # Load data
        self.load_products()

        # Focus
        self.focus_force()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _setup_ui(self):
        """Create complete UI layout"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure((0, 2), weight=1)  # Equal width for both tables
        main_frame.grid_columnconfigure(1, weight=0)  # Fixed width for buttons
        main_frame.grid_rowconfigure(2, weight=1)

        # === FILTERS SECTION ===
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        filter_frame.grid_columnconfigure((1, 2, 3, 4, 5), weight=1)

        # Filter label
        ctk.CTkLabel(filter_frame, text="Filtry:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        # Customer filter
        ctk.CTkLabel(filter_frame, text="Klient:").grid(row=0, column=1, sticky="w", padx=5)
        self.customer_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Wszystkie"],
            command=self.apply_filters,
            width=150
        )
        self.customer_filter.grid(row=0, column=1, sticky="ew", padx=(50, 5), pady=5)
        self.customer_filter.set("Wszystkie")

        # Material filter
        ctk.CTkLabel(filter_frame, text="Materiał:").grid(row=0, column=2, sticky="w", padx=5)
        self.material_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Wszystkie"],
            command=self.apply_filters,
            width=150
        )
        self.material_filter.grid(row=0, column=2, sticky="ew", padx=(60, 5), pady=5)
        self.material_filter.set("Wszystkie")

        # Thickness filter
        ctk.CTkLabel(filter_frame, text="Grubość:").grid(row=0, column=3, sticky="w", padx=5)
        self.thickness_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Wszystkie"],
            command=self.apply_filters,
            width=100
        )
        self.thickness_filter.grid(row=0, column=3, sticky="ew", padx=(60, 5), pady=5)
        self.thickness_filter.set("Wszystkie")

        # Name filter
        ctk.CTkLabel(filter_frame, text="Nazwa:").grid(row=0, column=4, sticky="w", padx=5)
        self.name_filter = ctk.CTkEntry(filter_frame, placeholder_text="Szukaj w nazwie...")
        self.name_filter.grid(row=0, column=4, sticky="ew", padx=(50, 5), pady=5)
        self.name_filter.bind("<KeyRelease>", lambda e: self.apply_filters())

        # Index filter
        ctk.CTkLabel(filter_frame, text="Indeks:").grid(row=0, column=5, sticky="w", padx=5)
        self.index_filter = ctk.CTkEntry(filter_frame, placeholder_text="Szukaj indeksu...")
        self.index_filter.grid(row=0, column=5, sticky="ew", padx=(50, 5), pady=5)
        self.index_filter.bind("<KeyRelease>", lambda e: self.apply_filters())

        # Clear filters button
        ctk.CTkButton(
            filter_frame,
            text="Wyczyść filtry",
            command=self.clear_filters,
            width=100
        ).grid(row=0, column=6, padx=5, pady=5)

        # === HEADERS ===
        # Left header
        left_header = ctk.CTkFrame(main_frame)
        left_header.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(
            left_header,
            text="Dostępne produkty",
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=10)
        self.left_count_label = ctk.CTkLabel(
            left_header,
            text="(0 produktów)",
            font=("Arial", 11)
        )
        self.left_count_label.pack(side="left", padx=5)

        # Show thumbnails checkbox for left table
        self.show_thumbnails_left_var = tk.BooleanVar(value=True)
        self.show_thumbnails_left_check = ctk.CTkCheckBox(
            left_header,
            text="Wyświetlaj miniatury",
            variable=self.show_thumbnails_left_var,
            command=self.populate_left_table
        )
        self.show_thumbnails_left_check.pack(side="right", padx=10)

        # Right header
        right_header = ctk.CTkFrame(main_frame)
        right_header.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(
            right_header,
            text="Wybrane produkty",
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=10)
        self.right_count_label = ctk.CTkLabel(
            right_header,
            text="(0 produktów)",
            font=("Arial", 11)
        )
        self.right_count_label.pack(side="left", padx=5)

        # Show thumbnails checkbox for right table
        self.show_thumbnails_right_var = tk.BooleanVar(value=True)
        self.show_thumbnails_right_check = ctk.CTkCheckBox(
            right_header,
            text="Wyświetlaj miniatury",
            variable=self.show_thumbnails_right_var,
            command=self.populate_right_table
        )
        self.show_thumbnails_right_check.pack(side="right", padx=10)

        # === LEFT TABLE (Available Products) ===
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1)

        # Create treeview
        columns = ('idx', 'name', 'material', 'thickness', 'customer')
        self.left_tree = ttk.Treeview(
            left_frame,
            columns=columns,
            show='tree headings',
            selectmode='extended'
        )

        # Configure columns
        self.left_tree.heading('#0', text='')
        self.left_tree.heading('idx', text='Indeks')
        self.left_tree.heading('name', text='Nazwa')
        self.left_tree.heading('material', text='Materiał')
        self.left_tree.heading('thickness', text='Grubość')
        self.left_tree.heading('customer', text='Klient')

        self.left_tree.column('#0', width=50, stretch=False)
        self.left_tree.column('idx', width=100)
        self.left_tree.column('name', width=200)
        self.left_tree.column('material', width=100)
        self.left_tree.column('thickness', width=80)
        self.left_tree.column('customer', width=150)

        # Scrollbars
        left_vscroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.left_tree.yview)
        left_hscroll = ttk.Scrollbar(left_frame, orient="horizontal", command=self.left_tree.xview)
        self.left_tree.configure(yscrollcommand=left_vscroll.set, xscrollcommand=left_hscroll.set)

        # Grid
        self.left_tree.grid(row=0, column=0, sticky="nsew")
        left_vscroll.grid(row=0, column=1, sticky="ns")
        left_hscroll.grid(row=1, column=0, sticky="ew")

        # Context menu
        self.left_menu = Menu(self.left_tree, tearoff=0)
        self.left_menu.add_command(label="Dodaj do wybranych", command=self.add_selected)
        self.left_menu.add_separator()
        self.left_menu.add_command(label="Podgląd", command=self.preview_left_product)

        self.left_tree.bind("<Button-3>", self.show_left_menu)
        self.left_tree.bind("<Double-1>", lambda e: self.add_selected())

        # === MIDDLE BUTTONS ===
        middle_frame = ctk.CTkFrame(main_frame)
        middle_frame.grid(row=2, column=1, sticky="ns", padx=10, pady=5)

        # Transfer buttons
        ctk.CTkButton(
            middle_frame,
            text="→",
            command=self.add_selected,
            width=50,
            font=("Arial", 16, "bold")
        ).pack(pady=(50, 10))

        ctk.CTkButton(
            middle_frame,
            text="⇒",
            command=self.add_all,
            width=50,
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ctk.CTkButton(
            middle_frame,
            text="←",
            command=self.remove_selected,
            width=50,
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ctk.CTkButton(
            middle_frame,
            text="⇐",
            command=self.remove_all,
            width=50,
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # === RIGHT TABLE (Selected Products) - EDITABLE ===
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=2, column=2, sticky="nsew", padx=5, pady=5)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        # Create editable treeview
        columns = ('idx', 'name', 'material', 'thickness', 'qty', 'price', 'total')
        self.right_tree = EditableTreeview(
            right_frame,
            columns=columns,
            editable_columns=['name', 'qty', 'price'],  # Editable columns
            on_edit_complete=self.on_cell_edited,
            show='tree headings',
            selectmode='extended'
        )

        # Configure columns
        self.right_tree.heading('#0', text='')
        self.right_tree.heading('idx', text='Indeks')
        self.right_tree.heading('name', text='Nazwa *')
        self.right_tree.heading('material', text='Materiał')
        self.right_tree.heading('thickness', text='Grubość')
        self.right_tree.heading('qty', text='Ilość *')
        self.right_tree.heading('price', text='Cena *')
        self.right_tree.heading('total', text='Razem')

        self.right_tree.column('#0', width=50, stretch=False)
        self.right_tree.column('idx', width=100)
        self.right_tree.column('name', width=200)
        self.right_tree.column('material', width=100)
        self.right_tree.column('thickness', width=80)
        self.right_tree.column('qty', width=60)
        self.right_tree.column('price', width=100)
        self.right_tree.column('total', width=100)

        # Scrollbars
        right_vscroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.right_tree.yview)
        right_hscroll = ttk.Scrollbar(right_frame, orient="horizontal", command=self.right_tree.xview)
        self.right_tree.configure(yscrollcommand=right_vscroll.set, xscrollcommand=right_hscroll.set)

        # Grid
        self.right_tree.grid(row=0, column=0, sticky="nsew")
        right_vscroll.grid(row=0, column=1, sticky="ns")
        right_hscroll.grid(row=1, column=0, sticky="ew")

        # Context menu for right table
        self.right_menu = Menu(self.right_tree, tearoff=0)
        self.right_menu.add_command(label="Edytuj", command=self.edit_selected_product)
        self.right_menu.add_command(label="Usuń z wybranych", command=self.remove_selected)
        self.right_menu.add_separator()
        self.right_menu.add_command(label="Podgląd", command=self.preview_right_product)

        self.right_tree.bind("<Button-3>", self.show_right_menu)

        # === SUMMARY SECTION ===
        summary_frame = ctk.CTkFrame(main_frame)
        summary_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Info label
        info_text = "* Podwójne kliknięcie na komórce w tabeli 'Wybrane produkty' umożliwia edycję: Nazwy, Ilości i Ceny"
        ctk.CTkLabel(
            summary_frame,
            text=info_text,
            font=("Arial", 10),
            text_color="gray60"
        ).pack(side="left", padx=10, pady=5)

        # Total value
        self.total_label = ctk.CTkLabel(
            summary_frame,
            text="Wartość zamówienia: 0.00 PLN",
            font=("Arial", 14, "bold"),
            text_color="green"
        )
        self.total_label.pack(side="right", padx=20, pady=5)

        # === ACTION BUTTONS ===
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        # Buttons
        ctk.CTkButton(
            button_frame,
            text="Zatwierdź wybór",
            command=self.on_confirm,
            fg_color="green",
            hover_color="darkgreen",
            width=150,
            height=35
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Anuluj",
            command=self.on_cancel,
            fg_color="red",
            hover_color="darkred",
            width=150,
            height=35
        ).pack(side="right", padx=5)

    def load_products(self):
        """Load products from database"""
        try:
            # Query products with related data
            response = self.db.client.table('products_catalog').select(
                '*',
                'materials_dict(name)',
                'customers(name, short_name)'
            ).eq('is_active', True).execute()

            self.all_products = response.data
            self.filtered_products = self.all_products.copy()

            # Load filter options
            self.load_filter_options()

            # Populate left table
            self.populate_left_table()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się załadować produktów: {e}")
            self.all_products = []
            self.filtered_products = []

    def load_filter_options(self):
        """Load unique values for filter dropdowns"""
        # Customers
        customers = set()
        materials = set()
        thicknesses = set()

        for product in self.all_products:
            # Customer
            if product.get('customers'):
                customer_name = product['customers'].get('short_name') or product['customers'].get('name')
                if customer_name:
                    customers.add(customer_name)

            # Material
            if product.get('materials_dict'):
                material_name = product['materials_dict'].get('name')
                if material_name:
                    materials.add(material_name)

            # Thickness
            if product.get('thickness_mm'):
                thicknesses.add(f"{product['thickness_mm']} mm")

        # Update comboboxes
        self.customer_filter.configure(values=["Wszystkie"] + sorted(list(customers)))
        self.material_filter.configure(values=["Wszystkie"] + sorted(list(materials)))
        self.thickness_filter.configure(values=["Wszystkie"] + sorted(list(thicknesses)))

    def apply_filters(self, *args):
        """Apply all active filters"""
        self.filtered_products = []

        customer_filter = self.customer_filter.get()
        material_filter = self.material_filter.get()
        thickness_filter = self.thickness_filter.get()
        name_filter = self.name_filter.get().lower()
        index_filter = self.index_filter.get().lower()

        for product in self.all_products:
            # Check customer filter
            if customer_filter != "Wszystkie":
                customer_name = ""
                if product.get('customers'):
                    customer_name = product['customers'].get('short_name') or product['customers'].get('name', "")
                if customer_name != customer_filter:
                    continue

            # Check material filter
            if material_filter != "Wszystkie":
                material_name = ""
                if product.get('materials_dict'):
                    material_name = product['materials_dict'].get('name', "")
                if material_name != material_filter:
                    continue

            # Check thickness filter
            if thickness_filter != "Wszystkie":
                thickness = f"{product.get('thickness_mm', 0)} mm"
                if thickness != thickness_filter:
                    continue

            # Check name filter
            if name_filter:
                product_name = product.get('name', '').lower()
                if name_filter not in product_name:
                    continue

            # Check index filter
            if index_filter:
                product_idx = (product.get('idx_code') or '').lower()
                if index_filter not in product_idx:
                    continue

            self.filtered_products.append(product)

        # Update display
        self.populate_left_table()

    def clear_filters(self):
        """Clear all filters"""
        self.customer_filter.set("Wszystkie")
        self.material_filter.set("Wszystkie")
        self.thickness_filter.set("Wszystkie")
        self.name_filter.delete(0, tk.END)
        self.index_filter.delete(0, tk.END)

        self.filtered_products = self.all_products.copy()
        self.populate_left_table()

    def populate_left_table(self):
        """Populate left table with filtered products"""
        # Clear current items
        self.left_tree.delete(*self.left_tree.get_children())

        # Store thumbnails to prevent garbage collection
        self.left_thumbnails = []

        # Add filtered products
        for product in self.filtered_products:
            # Skip if already selected
            if any(p.get('id') == product.get('id') for p in self.selected_products if p.get('id') and product.get('id')):
                continue

            # Get thumbnail only if checkbox is checked
            thumbnail = None
            if self.show_thumbnails_left_var.get():
                thumbnail = self.get_product_thumbnail(product)
                if thumbnail:
                    self.left_thumbnails.append(thumbnail)  # Keep reference

            # Prepare values
            idx = product.get('idx_code', '-')
            name = product.get('name', '-')
            material = ""
            if product.get('materials_dict'):
                material = product['materials_dict'].get('name', '-')
            thickness = f"{product.get('thickness_mm', 0)} mm" if product.get('thickness_mm') else "-"
            customer = ""
            if product.get('customers'):
                customer = product['customers'].get('short_name') or product['customers'].get('name', '-')

            # Insert item
            item = self.left_tree.insert(
                '', 'end',
                values=(idx, name, material, thickness, customer),
                image=thumbnail if thumbnail else '',
                tags=(product.get('id'),)
            )

        # Update count
        count = len(self.left_tree.get_children())
        self.left_count_label.configure(text=f"({count} produktów)")

    def populate_right_table(self):
        """Populate right table with selected products"""
        # Clear current items
        self.right_tree.delete(*self.right_tree.get_children())

        # Store thumbnails to prevent garbage collection
        self.right_thumbnails = []

        total_value = 0

        # Add selected products
        for product in self.selected_products:
            # Get thumbnail only if checkbox is checked
            thumbnail = None
            if self.show_thumbnails_right_var.get():
                thumbnail = self.get_product_thumbnail(product)
                if thumbnail:
                    self.right_thumbnails.append(thumbnail)  # Keep reference

            # Prepare values
            idx = product.get('idx_code', '-')
            name = product.get('name', '-')
            material = ""
            if product.get('materials_dict'):
                material = product['materials_dict'].get('name', '-')
            thickness = f"{product.get('thickness_mm', 0)} mm" if product.get('thickness_mm') else "-"

            # Get quantity and price
            qty = product.get('quantity', 1)
            price = product.get('unit_price', 0)
            if price == 0:
                # Calculate from costs if no unit price
                price = (product.get('material_laser_cost', 0) +
                        product.get('bending_cost', 0) +
                        product.get('additional_costs', 0))

            total = qty * price
            total_value += total

            # Format values
            qty_str = str(qty)
            price_str = f"{price:.2f}"
            total_str = f"{total:.2f}"

            # Insert item
            item = self.right_tree.insert(
                '', 'end',
                values=(idx, name, material, thickness, qty_str, price_str, total_str),
                image=thumbnail if thumbnail else '',
                tags=(product.get('id'),)
            )

        # Update count and total
        count = len(self.right_tree.get_children())
        self.right_count_label.configure(text=f"({count} produktów)")
        self.total_label.configure(text=f"Wartość zamówienia: {total_value:.2f} PLN")

    def get_product_thumbnail(self, product):
        """Get product thumbnail image"""
        try:
            # Use global thumbnail loader
            loader = get_thumbnail_loader()
            return loader.get_product_thumbnail(product, size=(40, 40))
        except Exception as e:
            print(f"Error loading thumbnail: {e}")
            return None

    def add_selected(self):
        """Add selected products from left to right table"""
        selected = self.left_tree.selection()

        for item in selected:
            # Get product ID from tags
            tags = self.left_tree.item(item, 'tags')
            if not tags:
                continue

            product_id = tags[0]

            # Find product in filtered list
            product = next((p for p in self.filtered_products if p.get('id') == product_id), None)
            if product:
                # Create copy with default quantity
                product_copy = product.copy()
                product_copy['quantity'] = 1

                # Calculate unit price
                unit_price = (product.get('material_laser_cost', 0) +
                            product.get('bending_cost', 0) +
                            product.get('additional_costs', 0))
                product_copy['unit_price'] = unit_price

                # Add to selected
                self.selected_products.append(product_copy)

        # Update tables
        self.populate_left_table()
        self.populate_right_table()

    def add_all(self):
        """Add all filtered products to selection"""
        for product in self.filtered_products:
            # Skip if already selected
            if any(p.get('id') == product.get('id') for p in self.selected_products if p.get('id') and product.get('id')):
                continue

            # Create copy with default quantity
            product_copy = product.copy()
            product_copy['quantity'] = 1

            # Calculate unit price
            unit_price = (product.get('material_laser_cost', 0) +
                        product.get('bending_cost', 0) +
                        product.get('additional_costs', 0))
            product_copy['unit_price'] = unit_price

            # Add to selected
            self.selected_products.append(product_copy)

        # Update tables
        self.populate_left_table()
        self.populate_right_table()

    def remove_selected(self):
        """Remove selected products from right table"""
        selected = self.right_tree.selection()

        products_to_remove = []
        for item in selected:
            # Get product ID from tags
            tags = self.right_tree.item(item, 'tags')
            if tags:
                product_id = tags[0]
                products_to_remove.append(product_id)

        # Remove products
        self.selected_products = [
            p for p in self.selected_products
            if p.get('id') not in products_to_remove
        ]

        # Update tables
        self.populate_left_table()
        self.populate_right_table()

    def remove_all(self):
        """Remove all selected products"""
        self.selected_products = []

        # Update tables
        self.populate_left_table()
        self.populate_right_table()

    def on_cell_edited(self, item, column, new_value):
        """Handle inline cell editing"""
        try:
            # Get product ID from tags
            tags = self.right_tree.item(item, 'tags')
            if not tags:
                return

            product_id = tags[0]

            # Find product in selected list
            product = next((p for p in self.selected_products if p.get('id') == product_id), None)
            if not product:
                return

            # Update product based on edited column
            if column == 'name':
                product['name'] = new_value
            elif column == 'qty':
                try:
                    qty = int(new_value)
                    if qty > 0:
                        product['quantity'] = qty
                except ValueError:
                    messagebox.showerror("Błąd", "Ilość musi być liczbą całkowitą większą od 0")
                    self.populate_right_table()
                    return
            elif column == 'price':
                try:
                    price = float(new_value.replace(',', '.').replace(' PLN', ''))
                    if price >= 0:
                        product['unit_price'] = price
                except ValueError:
                    messagebox.showerror("Błąd", "Cena musi być liczbą")
                    self.populate_right_table()
                    return

            # Recalculate and update display
            self.populate_right_table()

        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas edycji: {e}")
            self.populate_right_table()

    def edit_selected_product(self):
        """Open edit dialog for selected product"""
        selected = self.right_tree.selection()
        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz produkt do edycji")
            return

        # Get first selected item
        item = selected[0]
        tags = self.right_tree.item(item, 'tags')
        if not tags:
            return

        product_id = tags[0]

        # Find product
        product = next((p for p in self.selected_products if p.get('id') == product_id), None)
        if not product:
            return

        # Open edit dialog
        try:
            dialog = EnhancedPartEditDialogV4(
                self,
                self.db,
                part_data=product,
                edit_mode=True
            )

            self.wait_window(dialog)

            # If saved, update the product
            if hasattr(dialog, 'saved_data') and dialog.saved_data:
                # Update product with new data
                for key, value in dialog.saved_data.items():
                    product[key] = value

                # Refresh display
                self.populate_right_table()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć edytora: {e}")

    def preview_left_product(self):
        """Preview product from left table"""
        selected = self.left_tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.left_tree.item(item, 'tags')
        if not tags:
            return

        product_id = tags[0]
        product = next((p for p in self.filtered_products if p.get('id') == product_id), None)

        if product:
            self.show_product_preview(product)

    def preview_right_product(self):
        """Preview product from right table"""
        selected = self.right_tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = self.right_tree.item(item, 'tags')
        if not tags:
            return

        product_id = tags[0]
        product = next((p for p in self.selected_products if p.get('id') == product_id), None)

        if product:
            self.show_product_preview(product)

    def show_product_preview(self, product):
        """Show product preview dialog"""
        preview = ctk.CTkToplevel(self)
        preview.title(f"Podgląd: {product.get('name', 'Produkt')}")
        preview.geometry("600x400")

        # Create info text
        info_text = f"""
Indeks: {product.get('idx_code', '-')}
Nazwa: {product.get('name', '-')}
Kategoria: {product.get('category', '-')}

Materiał: {product.get('materials_dict', {}).get('name', '-') if product.get('materials_dict') else '-'}
Grubość: {product.get('thickness_mm', 0)} mm
Wymiary: {product.get('width_mm', 0)} x {product.get('height_mm', 0)} mm

Koszty:
- Materiał + Laser: {product.get('material_laser_cost', 0):.2f} PLN
- Gięcie: {product.get('bending_cost', 0):.2f} PLN
- Dodatkowe: {product.get('additional_costs', 0):.2f} PLN

Notatki: {product.get('notes', '-')}
        """

        text_widget = ctk.CTkTextbox(preview, width=550, height=350)
        text_widget.pack(padx=20, pady=20)
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")

        preview.focus_force()

    def show_left_menu(self, event):
        """Show context menu for left table"""
        # Select item under cursor
        item = self.left_tree.identify_row(event.y)
        if item:
            self.left_tree.selection_set(item)
            self.left_menu.post(event.x_root, event.y_root)

    def show_right_menu(self, event):
        """Show context menu for right table"""
        # Select item under cursor
        item = self.right_tree.identify_row(event.y)
        if item:
            self.right_tree.selection_set(item)
            self.right_menu.post(event.x_root, event.y_root)

    def on_confirm(self):
        """Confirm selection and return products"""
        if not self.selected_products:
            messagebox.showwarning("Uwaga", "Nie wybrano żadnych produktów")
            return

        # Call callback if provided
        if self.callback:
            self.callback(self.selected_products)

        self.destroy()

    def on_cancel(self):
        """Cancel and close dialog"""
        self.destroy()


# For backward compatibility
class ProductSelectorDialog(EnhancedProductSelectorDialog):
    """Alias for backward compatibility"""
    pass