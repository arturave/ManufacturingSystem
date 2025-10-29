#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product Selector Dialog for Orders/Quotes
Dual-table interface with filtering and transfer controls
"""

import customtkinter as ctk
from tkinter import messagebox, Menu
import tkinter as tk
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from PIL import Image, ImageTk

from image_processing import ImageProcessor, get_cached_image
from part_edit_enhanced import EnhancedPartEditDialog


class ProductSelectorDialog(ctk.CTkToplevel):
    """Product selector with dual tables for orders/quotes"""

    def __init__(self, parent, db, existing_parts: List[Dict] = None, callback: Callable = None):
        super().__init__(parent)
        self.db = db
        self.existing_parts = existing_parts or []
        self.callback = callback

        # Data storage
        self.all_products = []
        self.filtered_products = []
        self.selected_products = []  # Products selected for order/quote
        self.left_selection = []  # Selected items in left table
        self.right_selection = []  # Selected items in right table

        self.title("Wybór produktów do zamówienia/oferty")
        self.geometry("1400x800")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.load_products()
        self.load_existing_parts()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 700
        y = (self.winfo_screenheight() // 2) - 400
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI with dual tables"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="📦 Wybór produktów",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=10)

        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Filtruj:", width=60).pack(side="left", padx=5)
        self.filter_entry = ctk.CTkEntry(
            filter_frame,
            width=300,
            placeholder_text="Wpisz nazwę produktu..."
        )
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.bind("<KeyRelease>", self.apply_filter)

        ctk.CTkButton(
            filter_frame,
            text="🔍 Szukaj",
            width=100,
            command=self.apply_filter
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="❌ Wyczyść",
            width=100,
            command=self.clear_filter
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="➕ Nowy produkt",
            width=120,
            command=self.create_new_product,
            fg_color="#4CAF50"
        ).pack(side="right", padx=5)

        # Main content - dual tables
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left table - Available products
        left_container = ctk.CTkFrame(content_frame)
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left_container,
            text="Dostępne produkty",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        # Left table with scrollbar
        self.left_tree = self.create_treeview(left_container, "left")
        self.left_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Center controls
        control_frame = ctk.CTkFrame(content_frame)
        control_frame.pack(side="left", padx=10)

        # Transfer buttons
        button_width = 60
        button_height = 40

        ctk.CTkButton(
            control_frame,
            text="→",
            width=button_width,
            height=button_height,
            command=self.add_selected,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=5)

        ctk.CTkButton(
            control_frame,
            text="⇉",
            width=button_width,
            height=button_height,
            command=self.add_all,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=5)

        ctk.CTkButton(
            control_frame,
            text="←",
            width=button_width,
            height=button_height,
            command=self.remove_selected,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=5)

        ctk.CTkButton(
            control_frame,
            text="⇇",
            width=button_width,
            height=button_height,
            command=self.remove_all,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=5)

        # Separator
        ttk_separator = tk.Frame(control_frame, height=2, bg="#666666")
        ttk_separator.pack(fill="x", pady=20)

        ctk.CTkButton(
            control_frame,
            text="✚",
            width=button_width,
            height=button_height,
            command=self.duplicate_selected_right,
            font=ctk.CTkFont(size=20),
            fg_color="#9C27B0"
        ).pack(pady=5)

        ctk.CTkButton(
            control_frame,
            text="DEL",
            width=button_width,
            height=button_height,
            command=self.delete_selected_right,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#F44336"
        ).pack(pady=5)

        # Right table - Selected products
        right_container = ctk.CTkFrame(content_frame)
        right_container.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right_container,
            text="Produkty w zamówieniu/ofercie",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        # Right table with scrollbar
        self.right_tree = self.create_treeview(right_container, "right")
        self.right_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Summary info
        summary_frame = ctk.CTkFrame(right_container)
        summary_frame.pack(fill="x", padx=5, pady=5)

        self.summary_label = ctk.CTkLabel(
            summary_frame,
            text="Wybrano: 0 produktów | Łączna ilość: 0",
            font=ctk.CTkFont(size=12)
        )
        self.summary_label.pack(side="left", padx=10)

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            bottom_frame,
            text="✅ Zatwierdź wybór",
            width=150,
            height=40,
            command=self.confirm_selection,
            fg_color="#4CAF50"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            bottom_frame,
            text="❌ Anuluj",
            width=150,
            height=40,
            command=self.destroy
        ).pack(side="right", padx=10)

        self.status_label = ctk.CTkLabel(bottom_frame, text="Gotowy", anchor="w")
        self.status_label.pack(side="left", padx=20, fill="x", expand=True)

    def create_treeview(self, parent, side: str):
        """Create treeview widget with columns"""
        # Create frame for treeview and scrollbar
        tree_frame = ctk.CTkFrame(parent)

        # Create Treeview
        columns = ("idx", "name", "material", "thickness", "qty", "cost")
        tree = tk.ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="extended",
            height=20
        )

        # Define headings
        tree.heading("#0", text="")  # Icon column
        tree.heading("idx", text="Indeks")
        tree.heading("name", text="Nazwa")
        tree.heading("material", text="Materiał")
        tree.heading("thickness", text="Grubość")
        tree.heading("qty", text="Ilość")
        tree.heading("cost", text="Koszt")

        # Column configuration
        tree.column("#0", width=50, stretch=False)
        tree.column("idx", width=100, anchor="w")
        tree.column("name", width=250, anchor="w")
        tree.column("material", width=150, anchor="w")
        tree.column("thickness", width=80, anchor="center")
        tree.column("qty", width=60, anchor="center")
        tree.column("cost", width=100, anchor="e")

        # Scrollbars
        vsb = tk.ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = tk.ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        tree.bind("<Double-Button-1>", lambda e: self.on_double_click(e, side))
        tree.bind("<Button-3>", lambda e: self.show_context_menu(e, side))
        tree.bind("<<TreeviewSelect>>", lambda e: self.on_selection_change(e, side))

        # Style
        style = tk.ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white",
                       fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#3c3c3c", foreground="white",
                       borderwidth=1)
        style.map("Treeview", background=[("selected", "#4a4a4a")])

        return tree_frame

    def load_products(self):
        """Load all products from database"""
        try:
            catalog_products = []

            # Try to load from products_catalog if table exists
            try:
                catalog_response = self.db.client.table('products_catalog').select(
                    "*, materials_dict!material_id(name, category), customers!customer_id(name)"
                ).eq('is_active', True).order('name').execute()
                catalog_products = catalog_response.data or []

                # Mark source for each product
                for product in catalog_products:
                    product['_source'] = 'catalog'
            except Exception as catalog_error:
                # Table doesn't exist yet or other error - continue without catalog products
                print(f"Uwaga: Tabela products_catalog niedostępna: {catalog_error}")

            # Load products from parts table (existing order parts)
            # These can also be used as templates
            parts_response = self.db.client.table('parts').select(
                "*, materials_dict!material_id(name, category)"
            ).order('name').execute()

            parts_products = parts_response.data or []

            # Mark source for each product
            for product in parts_products:
                product['_source'] = 'parts'

            # Combine and remove duplicates (prefer catalog version)
            seen_codes = set()
            combined = []

            # Add catalog products first if we have any
            for product in catalog_products:
                if product.get('idx_code'):
                    seen_codes.add(product['idx_code'])
                combined.append(product)

            # Add parts that don't have matching idx_code in catalog
            for product in parts_products:
                idx_code = product.get('idx_code')
                if not idx_code or idx_code not in seen_codes:
                    combined.append(product)

            self.all_products = combined
            self.filtered_products = self.all_products
            self.populate_left_table()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować produktów:\n{e}")

    def load_existing_parts(self):
        """Load existing parts if editing order/quote"""
        if self.existing_parts:
            self.selected_products = self.existing_parts.copy()
            self.populate_right_table()
            self.update_summary()

    def populate_left_table(self):
        """Populate left table with filtered products"""
        # Clear existing items
        for item in self.left_tree.winfo_children()[0].get_children():
            self.left_tree.winfo_children()[0].delete(item)

        tree = self.left_tree.winfo_children()[0]

        # Add products
        for product in self.filtered_products:
            # Skip if already in right table
            if any(p['id'] == product['id'] for p in self.selected_products):
                continue

            # Prepare values
            idx = product.get('idx_code', '-')
            name = product.get('name', '-')
            material = product.get('materials_dict', {}).get('name', '-') if product.get('materials_dict') else '-'
            thickness = f"{product.get('thickness_mm', 0)} mm"
            qty = str(product.get('qty', 1))

            # Calculate total cost
            bending = product.get('bending_cost', 0) or 0
            additional = product.get('additional_costs', 0) or 0
            cost = f"{bending + additional:.2f} PLN"

            # Insert with icon
            icon = "📦" if product.get('graphic_low_res') else "📄"
            tree.insert(
                "", "end",
                text=icon,
                values=(idx, name, material, thickness, qty, cost),
                tags=(product['id'],)
            )

    def populate_right_table(self):
        """Populate right table with selected products"""
        # Clear existing items
        for item in self.right_tree.winfo_children()[0].get_children():
            self.right_tree.winfo_children()[0].delete(item)

        tree = self.right_tree.winfo_children()[0]

        # Add selected products
        for product in self.selected_products:
            idx = product.get('idx_code', '-')
            name = product.get('name', '-')

            # Handle material name - can be dict or string
            if isinstance(product.get('materials_dict'), dict):
                material = product['materials_dict'].get('name', '-')
            else:
                material = product.get('material_name', product.get('material', '-'))

            thickness = f"{product.get('thickness_mm', 0)} mm"
            qty = str(product.get('qty', 1))

            # Calculate cost
            bending = product.get('bending_cost', 0) or 0
            additional = product.get('additional_costs', 0) or 0
            cost = f"{bending + additional:.2f} PLN"

            icon = "✓"
            tree.insert(
                "", "end",
                text=icon,
                values=(idx, name, material, thickness, qty, cost),
                tags=(product.get('id', ''),)
            )

    def apply_filter(self, event=None):
        """Apply name filter to products"""
        search_text = self.filter_entry.get().lower()

        if search_text:
            self.filtered_products = [
                p for p in self.all_products
                if search_text in p.get('name', '').lower()
                or search_text in p.get('idx_code', '').lower()
            ]
        else:
            self.filtered_products = self.all_products

        self.populate_left_table()
        self.status_label.configure(text=f"Znaleziono: {len(self.filtered_products)} produktów")

    def clear_filter(self):
        """Clear filter"""
        self.filter_entry.delete(0, "end")
        self.apply_filter()

    def add_selected(self):
        """Add selected products from left to right"""
        tree = self.left_tree.winfo_children()[0]
        selected = tree.selection()

        if not selected:
            self.status_label.configure(text="Wybierz produkty do dodania")
            return

        added = 0
        for item in selected:
            # Get product ID from tags
            tags = tree.item(item)['tags']
            if tags:
                product_id = tags[0]
                # Find product
                product = next((p for p in self.filtered_products if p['id'] == product_id), None)
                if product and product not in self.selected_products:
                    self.selected_products.append(product.copy())
                    added += 1

        if added > 0:
            self.populate_left_table()
            self.populate_right_table()
            self.update_summary()
            self.status_label.configure(text=f"Dodano {added} produktów")

    def add_all(self):
        """Add all filtered products"""
        added = 0
        for product in self.filtered_products:
            if not any(p['id'] == product['id'] for p in self.selected_products):
                self.selected_products.append(product.copy())
                added += 1

        if added > 0:
            self.populate_left_table()
            self.populate_right_table()
            self.update_summary()
            self.status_label.configure(text=f"Dodano wszystkie produkty ({added})")

    def remove_selected(self):
        """Remove selected products from right"""
        tree = self.right_tree.winfo_children()[0]
        selected = tree.selection()

        if not selected:
            self.status_label.configure(text="Wybierz produkty do usunięcia")
            return

        removed = 0
        for item in selected:
            tags = tree.item(item)['tags']
            if tags:
                product_id = tags[0]
                self.selected_products = [p for p in self.selected_products if p.get('id') != product_id]
                removed += 1

        if removed > 0:
            self.populate_left_table()
            self.populate_right_table()
            self.update_summary()
            self.status_label.configure(text=f"Usunięto {removed} produktów")

    def remove_all(self):
        """Remove all products from right"""
        count = len(self.selected_products)
        self.selected_products = []
        self.populate_left_table()
        self.populate_right_table()
        self.update_summary()
        self.status_label.configure(text=f"Usunięto wszystkie produkty ({count})")

    def duplicate_selected_right(self):
        """Duplicate selected products in right table"""
        tree = self.right_tree.winfo_children()[0]
        selected = tree.selection()

        if not selected:
            self.status_label.configure(text="Wybierz produkty do duplikacji")
            return

        duplicated = 0
        for item in selected:
            values = tree.item(item)['values']
            tags = tree.item(item)['tags']

            if tags:
                product_id = tags[0]
                # Find original product
                original = next((p for p in self.selected_products if p.get('id') == product_id), None)
                if original:
                    # Create duplicate
                    duplicate = original.copy()
                    duplicate['id'] = f"{original['id']}_dup_{len(self.selected_products)}"
                    duplicate['is_duplicate'] = True
                    self.selected_products.append(duplicate)
                    duplicated += 1

        if duplicated > 0:
            self.populate_right_table()
            self.update_summary()
            self.status_label.configure(text=f"Zduplikowano {duplicated} produktów")

    def delete_selected_right(self):
        """Delete selected products from right table"""
        self.remove_selected()

    def on_double_click(self, event, side: str):
        """Handle double-click on table row"""
        if side == "left":
            self.add_selected()
        else:
            # Edit quantity dialog
            self.edit_product_quantity()

    def edit_product_quantity(self):
        """Edit quantity of selected product in right table"""
        tree = self.right_tree.winfo_children()[0]
        selected = tree.selection()

        if not selected or len(selected) != 1:
            return

        item = selected[0]
        tags = tree.item(item)['tags']

        if tags:
            product_id = tags[0]
            product = next((p for p in self.selected_products if p.get('id') == product_id), None)

            if product:
                # Create quantity dialog
                dialog = ctk.CTkToplevel(self)
                dialog.title("Edytuj ilość")
                dialog.geometry("300x150")
                dialog.transient(self)
                dialog.grab_set()

                # Center dialog
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - 150
                y = (dialog.winfo_screenheight() // 2) - 75
                dialog.geometry(f"+{x}+{y}")

                # Content
                ctk.CTkLabel(dialog, text=f"Produkt: {product['name']}", font=ctk.CTkFont(size=12)).pack(pady=10)
                ctk.CTkLabel(dialog, text="Ilość:").pack()

                qty_entry = ctk.CTkEntry(dialog, width=100)
                qty_entry.pack(pady=5)
                qty_entry.insert(0, str(product.get('qty', 1)))
                qty_entry.focus()

                def save_qty():
                    try:
                        new_qty = int(qty_entry.get())
                        if new_qty > 0:
                            product['qty'] = new_qty
                            self.populate_right_table()
                            self.update_summary()
                            dialog.destroy()
                        else:
                            messagebox.showwarning("Uwaga", "Ilość musi być większa od 0", parent=dialog)
                    except ValueError:
                        messagebox.showwarning("Uwaga", "Nieprawidłowa wartość", parent=dialog)

                ctk.CTkButton(dialog, text="Zapisz", command=save_qty).pack(pady=10)

    def show_context_menu(self, event, side: str):
        """Show context menu for table"""
        # Get the tree widget
        if side == "left":
            tree = self.left_tree.winfo_children()[0]
        else:
            tree = self.right_tree.winfo_children()[0]

        # Select item under cursor
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)

            # Create context menu
            menu = Menu(self, tearoff=0)
            menu.configure(bg="#3c3c3c", fg="white", activebackground="#4a4a4a")

            if side == "left":
                menu.add_command(label="➡️ Dodaj do zamówienia", command=self.add_selected)
                menu.add_separator()
                menu.add_command(label="🔍 Pokaż szczegóły", command=lambda: self.show_product_details(side))
                menu.add_command(label="✏️ Edytuj produkt", command=lambda: self.edit_product(side))
            else:
                menu.add_command(label="📝 Zmień ilość", command=self.edit_product_quantity)
                menu.add_command(label="✚ Duplikuj", command=self.duplicate_selected_right)
                menu.add_separator()
                menu.add_command(label="🔍 Pokaż szczegóły", command=lambda: self.show_product_details(side))
                menu.add_separator()
                menu.add_command(label="🗑️ Usuń z zamówienia", command=self.remove_selected)

            menu.post(event.x_root, event.y_root)

    def show_product_details(self, side: str):
        """Show product details dialog"""
        if side == "left":
            tree = self.left_tree.winfo_children()[0]
            products = self.filtered_products
        else:
            tree = self.right_tree.winfo_children()[0]
            products = self.selected_products

        selected = tree.selection()
        if not selected:
            return

        item = selected[0]
        tags = tree.item(item)['tags']

        if tags:
            product_id = tags[0]
            product = next((p for p in products if p.get('id') == product_id), None)

            if product:
                # Import and show detail dialog
                from products_module import ProductDetailDialog
                detail_dialog = ProductDetailDialog(self, self.db, product)

    def edit_product(self, side: str):
        """Edit product in database"""
        if side == "left":
            tree = self.left_tree.winfo_children()[0]
            products = self.filtered_products
        else:
            tree = self.right_tree.winfo_children()[0]
            products = self.selected_products

        selected = tree.selection()
        if not selected or len(selected) != 1:
            return

        item = selected[0]
        tags = tree.item(item)['tags']

        if tags:
            product_id = tags[0]
            product = next((p for p in products if p.get('id') == product_id), None)

            if product:
                # Open edit dialog
                edit_dialog = EnhancedPartEditDialog(
                    self,
                    self.db,
                    [],  # Empty parts list for standalone edit
                    part_data=product,
                    part_index=None,
                    order_id=None
                )
                self.wait_window(edit_dialog)

                # Reload products after edit
                self.load_products()

    def on_selection_change(self, event, side: str):
        """Handle selection change in tables"""
        if side == "left":
            tree = self.left_tree.winfo_children()[0]
            self.left_selection = tree.selection()
        else:
            tree = self.right_tree.winfo_children()[0]
            self.right_selection = tree.selection()

    def update_summary(self):
        """Update summary information"""
        total_products = len(self.selected_products)
        total_qty = sum(p.get('qty', 1) for p in self.selected_products)
        total_cost = sum(
            (p.get('bending_cost', 0) or 0) + (p.get('additional_costs', 0) or 0)
            for p in self.selected_products
        )

        self.summary_label.configure(
            text=f"Wybrano: {total_products} produktów | Łączna ilość: {total_qty} | Koszt: {total_cost:.2f} PLN"
        )

    def create_new_product(self):
        """Create new product"""
        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],  # Empty parts list
            part_data=None,
            part_index=None,
            order_id=None
        )
        self.wait_window(dialog)

        # Reload products if new product was created
        if hasattr(dialog, 'part_data') and dialog.part_data:
            self.load_products()

    def confirm_selection(self):
        """Confirm selection and return to parent"""
        if not self.selected_products:
            result = messagebox.askyesno(
                "Brak produktów",
                "Nie wybrano żadnych produktów.\nCzy chcesz kontynuować?"
            )
            if not result:
                return

        # Prepare data for return
        result_parts = []
        for product in self.selected_products:
            part_data = {
                'idx_code': product.get('idx_code', ''),
                'name': product.get('name', ''),
                'material': product.get('material_name') or product.get('materials_dict', {}).get('name', ''),
                'material_id': product.get('material_id'),
                'thickness_mm': product.get('thickness_mm', 0),
                'qty': product.get('qty', 1),
                'bending_cost': product.get('bending_cost', 0),
                'additional_costs': product.get('additional_costs', 0),
                'graphic_high_res': product.get('graphic_high_res'),
                'graphic_low_res': product.get('graphic_low_res'),
                'documentation_path': product.get('documentation_path')
            }
            result_parts.append(part_data)

        # Call callback if provided
        if self.callback:
            self.callback(result_parts)

        self.destroy()