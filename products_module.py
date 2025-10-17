#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Products Management Module
Comprehensive product/parts management with filters, search, and graphics display
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image, ImageTk

from image_processing import ImageProcessor, get_cached_image
from materials_dict_module import MaterialsDictDialog
from part_edit_enhanced import EnhancedPartEditDialog


class ProductsWindow(ctk.CTkToplevel):
    """Main products management window with filters and product list"""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.products_data = []
        self.filtered_products = []
        self.selected_product_id = None

        self.title("Zarządzanie produktami (detalami)")
        self.geometry("1400x800")

        # Make modal
        self.transient(parent)

        self.setup_ui()
        self.load_products()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 700
        y = (self.winfo_screenheight() // 2) - 400
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="📦 Zarządzanie produktami",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=10)

        # Header buttons
        btn_frame = ctk.CTkFrame(header)
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="➕ Dodaj produkt",
            width=130,
            command=self.add_product,
            fg_color="#4CAF50"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="📋 Słownik materiałów",
            width=150,
            command=self.open_materials_dict
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🔄 Odśwież",
            width=100,
            command=self.load_products
        ).pack(side="left", padx=5)

        # Filters frame
        filters_frame = ctk.CTkFrame(self)
        filters_frame.pack(fill="x", padx=10, pady=5)

        # Row 1: Basic filters
        row1 = ctk.CTkFrame(filters_frame)
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Nazwa:", width=80).pack(side="left", padx=5)
        self.name_filter = ctk.CTkEntry(row1, width=200, placeholder_text="Szukaj nazwy...")
        self.name_filter.pack(side="left", padx=5)

        ctk.CTkLabel(row1, text="Materiał:", width=80).pack(side="left", padx=5)
        self.material_filter = ctk.CTkComboBox(row1, width=200, values=["Wszystkie"])
        self.material_filter.pack(side="left", padx=5)

        ctk.CTkLabel(row1, text="Grubość od:", width=80).pack(side="left", padx=5)
        self.thickness_from = ctk.CTkEntry(row1, width=80, placeholder_text="0")
        self.thickness_from.pack(side="left", padx=5)

        ctk.CTkLabel(row1, text="do:", width=30).pack(side="left")
        self.thickness_to = ctk.CTkEntry(row1, width=80, placeholder_text="100")
        self.thickness_to.pack(side="left", padx=5)

        # Row 2: Advanced filters
        row2 = ctk.CTkFrame(filters_frame)
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Klient:", width=80).pack(side="left", padx=5)
        self.customer_filter = ctk.CTkComboBox(row2, width=200, values=["Wszyscy"])
        self.customer_filter.pack(side="left", padx=5)

        ctk.CTkLabel(row2, text="Data od:", width=80).pack(side="left", padx=5)
        self.date_from = ctk.CTkEntry(row2, width=120, placeholder_text="RRRR-MM-DD")
        self.date_from.pack(side="left", padx=5)

        ctk.CTkLabel(row2, text="do:", width=30).pack(side="left")
        self.date_to = ctk.CTkEntry(row2, width=120, placeholder_text="RRRR-MM-DD")
        self.date_to.pack(side="left", padx=5)

        # Show duplicates only checkbox
        self.show_duplicates_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            row2,
            text="Tylko duplikaty",
            variable=self.show_duplicates_var
        ).pack(side="left", padx=10)

        # Apply filters button
        ctk.CTkButton(
            row2,
            text="🔍 Filtruj",
            width=100,
            command=self.apply_filters,
            fg_color="#2196F3"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            row2,
            text="❌ Wyczyść",
            width=100,
            command=self.clear_filters
        ).pack(side="right", padx=5)

        # Products list
        list_container = ctk.CTkFrame(self)
        list_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollable frame for products
        self.products_scroll = ctk.CTkScrollableFrame(list_container)
        self.products_scroll.pack(fill="both", expand=True)

        # Headers
        headers_frame = ctk.CTkFrame(self.products_scroll)
        headers_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(headers_frame, text="", width=80).pack(side="left", padx=5)  # Image
        ctk.CTkLabel(headers_frame, text="Indeks", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Nazwa", width=200, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Materiał", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Grubość", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Ilość", width=60, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Klient", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Zamówienie", width=120, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Data", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        # Products container
        self.products_container = ctk.CTkFrame(self.products_scroll)
        self.products_container.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = ctk.CTkLabel(self, text="Gotowy", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=5)

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
        """Load all products from database"""
        try:
            self.status_bar.configure(text="Ładowanie produktów...")

            # Load parts with joined data
            response = self.db.client.table('v_parts_full').select("*").order('created_at', desc=True).execute()
            self.products_data = response.data
            self.filtered_products = self.products_data

            self.display_products(self.filtered_products)
            self.status_bar.configure(text=f"Załadowano {len(self.products_data)} produktów")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować produktów:\n{e}")
            self.status_bar.configure(text="Błąd ładowania")

    def apply_filters(self):
        """Apply filters to product list"""
        filtered = []

        # Get filter values
        name_search = self.name_filter.get().lower()
        material_name = self.material_filter.get()
        thickness_from_str = self.thickness_from.get().strip()
        thickness_to_str = self.thickness_to.get().strip()
        customer_name = self.customer_filter.get()
        date_from_str = self.date_from.get().strip()
        date_to_str = self.date_to.get().strip()
        show_duplicates = self.show_duplicates_var.get()

        # Parse thickness
        thickness_from = float(thickness_from_str) if thickness_from_str else None
        thickness_to = float(thickness_to_str) if thickness_to_str else None

        # Filter products
        for product in self.products_data:
            # Name filter
            if name_search and name_search not in product.get('name', '').lower():
                continue

            # Material filter
            if material_name != "Wszystkie" and product.get('material_name') != material_name:
                continue

            # Thickness filter
            thickness = product.get('thickness_mm')
            if thickness is not None:
                if thickness_from is not None and thickness < thickness_from:
                    continue
                if thickness_to is not None and thickness > thickness_to:
                    continue

            # Customer filter
            if customer_name != "Wszyscy" and product.get('customer_name') != customer_name:
                continue

            # Date filter
            created_at = product.get('created_at')
            if created_at:
                try:
                    product_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    if date_from_str:
                        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                        if product_date < date_from:
                            continue
                    if date_to_str:
                        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                        if product_date > date_to:
                            continue
                except:
                    pass

            # Duplicates filter
            if show_duplicates and product.get('duplicate_number', 0) == 0:
                continue

            filtered.append(product)

        self.filtered_products = filtered
        self.display_products(self.filtered_products)
        self.status_bar.configure(text=f"Znaleziono {len(filtered)} produktów")

    def clear_filters(self):
        """Clear all filters"""
        self.name_filter.delete(0, "end")
        self.material_filter.set("Wszystkie")
        self.thickness_from.delete(0, "end")
        self.thickness_to.delete(0, "end")
        self.customer_filter.set("Wszyscy")
        self.date_from.delete(0, "end")
        self.date_to.delete(0, "end")
        self.show_duplicates_var.set(False)

        self.filtered_products = self.products_data
        self.display_products(self.filtered_products)
        self.status_bar.configure(text=f"Wyświetlono {len(self.products_data)} produktów")

    def display_products(self, products: List[Dict]):
        """Display products in the list"""
        # Clear existing widgets
        for widget in self.products_container.winfo_children():
            widget.destroy()

        # Display each product
        for product in products:
            self.create_product_row(product)

    def create_product_row(self, product: Dict):
        """Create a row for a product"""
        row = ctk.CTkFrame(self.products_container)
        row.pack(fill="x", pady=2)

        # Make row clickable
        row.bind("<Button-1>", lambda e, p=product: self.select_product(p))
        row.bind("<Double-Button-1>", lambda e, p=product: self.view_product_details(p))
        row.bind("<Button-3>", lambda e, p=product: self.show_context_menu(e, p))

        # Image thumbnail
        image_frame = ctk.CTkLabel(row, text="", width=80, height=60)
        image_frame.pack(side="left", padx=5)
        image_frame.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Try to load thumbnail
        if product.get('graphic_low_res'):
            try:
                img = get_cached_image(product['graphic_low_res'])
                if img:
                    photo = ImageProcessor.create_photoimage(img, (70, 50))
                    image_frame.configure(image=photo)
                    image_frame.image = photo
            except:
                pass

        # Index
        idx_label = ctk.CTkLabel(row, text=product.get('idx_code', '-'), width=100, anchor="w")
        idx_label.pack(side="left", padx=5)
        idx_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Name
        name_text = product.get('name', '-')
        if product.get('duplicate_number', 0) > 0:
            name_text = f"{name_text} [DUP-{product['duplicate_number']}]"
            name_color = "#ff9800"
        else:
            name_color = None

        name_label = ctk.CTkLabel(row, text=name_text, width=200, anchor="w", text_color=name_color)
        name_label.pack(side="left", padx=5)
        name_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Material
        material_label = ctk.CTkLabel(row, text=product.get('material_name', '-'), width=150, anchor="w")
        material_label.pack(side="left", padx=5)
        material_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Thickness
        thickness_text = f"{product.get('thickness_mm', '-')} mm" if product.get('thickness_mm') else "-"
        thickness_label = ctk.CTkLabel(row, text=thickness_text, width=80, anchor="w")
        thickness_label.pack(side="left", padx=5)
        thickness_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Quantity
        qty_label = ctk.CTkLabel(row, text=str(product.get('qty', '-')), width=60, anchor="w")
        qty_label.pack(side="left", padx=5)
        qty_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Customer (from joined order data)
        # Note: This requires proper view/join in database
        customer_text = "N/A"  # Placeholder
        customer_label = ctk.CTkLabel(row, text=customer_text, width=150, anchor="w")
        customer_label.pack(side="left", padx=5)
        customer_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Order number
        order_text = "N/A"  # Placeholder
        order_label = ctk.CTkLabel(row, text=order_text, width=120, anchor="w")
        order_label.pack(side="left", padx=5)
        order_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

        # Date
        date_text = "-"
        if product.get('created_at'):
            try:
                date_obj = datetime.fromisoformat(product['created_at'].replace('Z', '+00:00'))
                date_text = date_obj.strftime('%Y-%m-%d')
            except:
                pass

        date_label = ctk.CTkLabel(row, text=date_text, width=100, anchor="w")
        date_label.pack(side="left", padx=5)
        date_label.bind("<Button-1>", lambda e, p=product: self.select_product(p))

    def select_product(self, product: Dict):
        """Select a product"""
        self.selected_product_id = product['id']
        # Visual feedback could be added here
        self.status_bar.configure(text=f"Wybrano: {product.get('name')} ({product.get('idx_code')})")

    def view_product_details(self, product: Dict):
        """View product details (double-click)"""
        # Create a detail view dialog
        detail_window = ProductDetailDialog(self, self.db, product)

    def open_materials_dict(self):
        """Open materials dictionary"""
        dialog = MaterialsDictDialog(self, self.db)
        self.wait_window(dialog)

    def add_product(self):
        """Add new product"""
        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],  # Empty parts list for new product
            part_data=None,
            part_index=None,
            order_id=None
        )
        self.wait_window(dialog)

        # Reload products after adding
        if hasattr(dialog, 'part_data') and dialog.part_data:
            # Save to database
            # Save to database
            try:
                part_data = dialog.part_data
                response = self.db.client.table('parts').insert({
                    'name': part_data['name'],
                    'material_id': part_data.get('material_id'),
                    'thickness_mm': part_data.get('thickness_mm'),
                    'qty': part_data.get('qty', 1),
                    'bending_cost': part_data.get('bending_cost', 0),
                    'additional_costs': part_data.get('additional_costs', 0),
                    'graphic_high_res': part_data.get('graphic_high_res'),
                    'graphic_low_res': part_data.get('graphic_low_res'),
                    'documentation_path': part_data.get('documentation_path')
                }).execute()

                messagebox.showinfo("Sukces", "Produkt został dodany")
                self.load_products()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można dodać produktu:\n{e}")

    def edit_product(self, product: Dict):
        """Edit selected product"""
        dialog = EnhancedPartEditDialog(
            self,
            self.db,
            [],
            part_data=product,
            part_index=None,
            order_id=None
        )
        self.wait_window(dialog)

        # Reload products after edit
        if hasattr(dialog, 'part_data') and dialog.part_data:
            self.load_products()

    def duplicate_product(self, product: Dict):
        """Duplicate selected product"""
        try:
            # Create copy of product
            new_product = product.copy()
            new_product.pop('id', None)  # Remove ID
            new_product.pop('idx_code', None)  # Remove index (will be auto-generated)
            new_product['name'] = f"{product['name']} - kopia"

            # Save to database
            response = self.db.client.table('parts').insert(new_product).execute()

            messagebox.showinfo("Sukces", "Produkt został zduplikowany")
            self.load_products()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zduplikować produktu:\n{e}")

    def delete_product(self, product: Dict):
        """Delete selected product"""
        result = messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć produkt:\n{product.get('name')}?"
        )

        if result:
            try:
                self.db.client.table('parts').delete().eq('id', product['id']).execute()
                messagebox.showinfo("Sukces", "Produkt został usunięty")
                self.load_products()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można usunąć produktu:\n{e}")

    def show_context_menu(self, event, product: Dict):
        """Show context menu for product row"""
        # Import tkinter Menu
        from tkinter import Menu

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


class ProductDetailDialog(ctk.CTkToplevel):
    """Dialog showing detailed product information"""

    def __init__(self, parent, db, product: Dict):
        super().__init__(parent)
        self.db = db
        self.product = product

        self.title(f"Szczegóły produktu: {product.get('name')}")
        self.geometry("900x700")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 450
        y = (self.winfo_screenheight() // 2) - 350
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text=f"📦 {self.product.get('name')}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=10)

        # Main content
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # Left side - Image
        left_frame = ctk.CTkFrame(content)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        image_label = ctk.CTkLabel(left_frame, text="")
        image_label.pack(pady=10)

        # Try to load high-res image
        if self.product.get('graphic_high_res'):
            try:
                img = get_cached_image(self.product['graphic_high_res'])
                if img:
                    photo = ImageProcessor.create_photoimage(img, (400, 400))
                    image_label.configure(image=photo)
                    image_label.image = photo
            except:
                placeholder = ImageProcessor.create_placeholder_image((400, 400))
                photo = ImageTk.PhotoImage(placeholder)
                image_label.configure(image=photo)
                image_label.image = photo
        else:
            placeholder = ImageProcessor.create_placeholder_image((400, 400))
            photo = ImageTk.PhotoImage(placeholder)
            image_label.configure(image=photo)
            image_label.image = photo

        # Right side - Details
        right_frame = ctk.CTkScrollableFrame(content)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Basic info
        self.add_detail_row(right_frame, "Indeks:", self.product.get('idx_code', '-'))
        self.add_detail_row(right_frame, "Nazwa:", self.product.get('name', '-'))
        self.add_detail_row(right_frame, "Materiał:", self.product.get('material_name', '-'))
        self.add_detail_row(right_frame, "Kategoria materiału:", self.product.get('material_category', '-'))
        self.add_detail_row(right_frame, "Grubość:", f"{self.product.get('thickness_mm', '-')} mm")
        self.add_detail_row(right_frame, "Ilość:", str(self.product.get('qty', '-')))
        self.add_detail_row(right_frame, "Koszt gięcia:", f"{self.product.get('bending_cost', 0):.2f} PLN")
        self.add_detail_row(right_frame, "Koszty dodatkowe:", f"{self.product.get('additional_costs', 0):.2f} PLN")

        if self.product.get('duplicate_number', 0) > 0:
            self.add_detail_row(right_frame, "Duplikat:", f"Numer {self.product['duplicate_number']}", text_color="#ff9800")

        # Documentation
        if self.product.get('documentation_path'):
            self.add_detail_row(right_frame, "Dokumentacja:", Path(self.product['documentation_path']).name)

        # Change history
        if self.product.get('change_history'):
            ctk.CTkLabel(right_frame, text="\nHistoria zmian:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=5)
            # TODO: Display change history from JSONB

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Zamknij",
            width=150,
            command=self.destroy
        ).pack(side="right", padx=5)

    def add_detail_row(self, parent, label: str, value: str, text_color=None):
        """Add a detail row"""
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(row, text=label, width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=value, anchor="w", text_color=text_color).pack(side="left", padx=5, fill="x", expand=True)
