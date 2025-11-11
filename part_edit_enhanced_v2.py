#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Part Edit Dialog V2 - z integracją podglądu 2D/3D
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any
from tkinter import messagebox, filedialog
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

# Import systemu podglądu
from integrated_viewer import (
    EnhancedFilePreviewFrame,
    ThumbnailGenerator,
    ViewerPopup
)

from image_processing import ImageProcessor, get_cached_image
from materials_dict_module import MaterialSelector


class EnhancedPartEditDialog(ctk.CTkToplevel):
    """Enhanced dialog V2 z podglądem 2D/3D i generowaniem miniatur"""

# Alias dla kompatybilności
EnhancedPartEditDialogV2 = EnhancedPartEditDialog

    def __init__(self, parent, db, parts_list, part_data=None, part_index=None, order_id=None):
        super().__init__(parent)
        self.db = db
        self.parts_list = parts_list
        self.part_data_original = part_data
        self.part_index = part_index
        self.order_id = order_id

        # Ścieżki do plików
        self.cad_2d_file = None
        self.cad_3d_file = None
        self.user_image_file = None
        self.thumbnail_data = None
        self.preview_4k_data = None

        # Zmienne dla radio buttons
        self.graphic_source_var = tk.StringVar(value="")

        # Store references to prevent garbage collection
        self.photo_references = []

        self.title("Edycja detalu V2" if part_data else "Nowy detal V2")
        self.geometry("1200x700")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Load existing data if editing
        if part_data:
            self.load_part_data()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 600
        y = (self.winfo_screenheight() // 2) - 350
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components"""
        # Create main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Form fields
        left_frame = ctk.CTkScrollableFrame(main_container, width=400)
        left_frame.pack(side="left", fill="y", padx=5)

        # Title
        ctk.CTkLabel(
            left_frame,
            text="📝 Dane produktu",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=10)

        # Index field (auto-generated)
        ctk.CTkLabel(left_frame, text="Indeks (auto):", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.idx_entry = ctk.CTkEntry(left_frame, width=350, height=35, state="disabled")
        self.idx_entry.pack(pady=5)

        # Customer field (when creating standalone product)
        if not self.order_id:
            ctk.CTkLabel(left_frame, text="Klient:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)

            # Get customers list
            customers_response = self.db.client.table('customers').select('id, name').order('name').execute()
            customer_names = ['Bez klienta'] + [c['name'] for c in customers_response.data]
            self.customer_map = {c['name']: c['id'] for c in customers_response.data}

            self.customer_combo = ctk.CTkComboBox(
                left_frame,
                width=350,
                height=35,
                values=customer_names
            )
            self.customer_combo.set('Bez klienta')
            self.customer_combo.pack(pady=5)

        # Name field
        ctk.CTkLabel(left_frame, text="Nazwa detalu*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.name_entry = ctk.CTkEntry(left_frame, width=350, height=35)
        self.name_entry.pack(pady=5)

        # Material selector
        ctk.CTkLabel(left_frame, text="Materiał*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.material_selector = MaterialSelector(left_frame, self.db, on_select_callback=None)
        self.material_selector.pack(pady=5, anchor="w")

        # Thickness field
        ctk.CTkLabel(left_frame, text="Grubość [mm]*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.thickness_entry = ctk.CTkEntry(left_frame, width=200, height=35)
        self.thickness_entry.pack(pady=5, anchor="w")

        # Info about qty
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        info_frame.pack(pady=5, anchor="w", fill="x")
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Ilość będzie określana przy dodawaniu do zamówienia",
            text_color="#888888",
            font=ctk.CTkFont(size=12, slant="italic")
        ).pack(anchor="w")

        # Bending cost
        ctk.CTkLabel(left_frame, text="Koszt gięcia [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.bending_cost_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.bending_cost_entry.pack(pady=5, anchor="w")

        # Additional costs
        ctk.CTkLabel(left_frame, text="Koszty dodatkowe [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.additional_costs_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.additional_costs_entry.pack(pady=5, anchor="w")

        # Right side - Graphics previews
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Title
        ctk.CTkLabel(
            right_frame,
            text="🖼️ Grafiki i pliki CAD",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        # Preview frames container
        preview_container = ctk.CTkFrame(right_frame)
        preview_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 2D CAD Preview
        self.frame_2d = EnhancedFilePreviewFrame(
            preview_container,
            "Plik 2D (DXF/DWG)",
            ['.dxf', '.dwg'],
            self.graphic_source_var,
            "2D"
        )
        self.frame_2d.pack(side="left", padx=10, fill="y")

        # 3D CAD Preview
        self.frame_3d = EnhancedFilePreviewFrame(
            preview_container,
            "Plik 3D (STEP/STL)",
            ['.step', '.stp', '.iges', '.igs', '.stl'],
            self.graphic_source_var,
            "3D"
        )
        self.frame_3d.pack(side="left", padx=10, fill="y")

        # User Image Preview
        self.frame_user = EnhancedFilePreviewFrame(
            preview_container,
            "Grafika użytkownika",
            ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
            self.graphic_source_var,
            "USER"
        )
        self.frame_user.pack(side="left", padx=10, fill="y")

        # Info about selected source
        info_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        )
        info_label.pack(pady=5)

        def update_source_info(*args):
            source = self.graphic_source_var.get()
            if source:
                info_label.configure(text=f"✓ Główne źródło grafiki: {source}")
            else:
                info_label.configure(text="⚠️ Wybierz źródło grafiki")

        self.graphic_source_var.trace('w', update_source_info)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", side="bottom", padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="✓ Zapisz",
            width=150,
            command=self.save_part,
            fg_color="#4CAF50"
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="✗ Anuluj",
            width=150,
            command=self.destroy,
            fg_color="#f44336"
        ).pack(side="right", padx=5)

        # Generate thumbnails button
        ctk.CTkButton(
            button_frame,
            text="🖼️ Generuj miniatury",
            width=150,
            command=self.generate_all_thumbnails
        ).pack(side="left", padx=5)

    def load_part_data(self):
        """Load existing part data into form"""
        if not self.part_data_original:
            return

        # Basic fields
        if self.part_data_original.get('idx_code'):
            self.idx_entry.configure(state="normal")
            self.idx_entry.delete(0, "end")
            self.idx_entry.insert(0, self.part_data_original['idx_code'])
            self.idx_entry.configure(state="disabled")

        self.name_entry.insert(0, self.part_data_original.get('name', ''))
        self.thickness_entry.insert(0, str(self.part_data_original.get('thickness_mm', '')))

        # Material
        if self.part_data_original.get('material_id'):
            self.material_selector.set_material(self.part_data_original['material_id'])

        # Costs
        if self.part_data_original.get('bending_cost'):
            self.bending_cost_entry.insert(0, str(self.part_data_original['bending_cost']))
        if self.part_data_original.get('additional_costs'):
            self.additional_costs_entry.insert(0, str(self.part_data_original['additional_costs']))

        # Graphics source
        if self.part_data_original.get('primary_graphic_source'):
            self.graphic_source_var.set(self.part_data_original['primary_graphic_source'])

        # File paths
        if self.part_data_original.get('cad_2d_file'):
            self.frame_2d.file_path = self.part_data_original['cad_2d_file']
            self.frame_2d.file_label.configure(text=Path(self.part_data_original['cad_2d_file']).name)

        if self.part_data_original.get('cad_3d_file'):
            self.frame_3d.file_path = self.part_data_original['cad_3d_file']
            self.frame_3d.file_label.configure(text=Path(self.part_data_original['cad_3d_file']).name)

        if self.part_data_original.get('user_image_file'):
            self.frame_user.file_path = self.part_data_original['user_image_file']
            self.frame_user.file_label.configure(text=Path(self.part_data_original['user_image_file']).name)

    def generate_all_thumbnails(self):
        """Generuj wszystkie miniatury"""
        generated = []

        # 2D CAD
        if self.frame_2d.file_path:
            self.frame_2d.generate_thumbnail()
            if self.frame_2d.thumbnail_data:
                generated.append("2D")

        # 3D CAD
        if self.frame_3d.file_path:
            self.frame_3d.generate_thumbnail()
            if self.frame_3d.thumbnail_data:
                generated.append("3D")

        # User image
        if self.frame_user.file_path:
            self.frame_user.generate_thumbnail()
            if self.frame_user.thumbnail_data:
                generated.append("User")

        if generated:
            messagebox.showinfo("Sukces", f"Wygenerowano miniatury: {', '.join(generated)}")
        else:
            messagebox.showwarning("Uwaga", "Brak plików do wygenerowania miniatur")

    def save_part(self):
        """Save part data"""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Błąd", "Nazwa detalu jest wymagana")
            return

        material_id = self.material_selector.selected_material_id
        if not material_id:
            messagebox.showerror("Błąd", "Materiał jest wymagany")
            return

        try:
            thickness = float(self.thickness_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowa wartość grubości")
            return

        # Get costs
        try:
            bending_cost = float(self.bending_cost_entry.get().strip() or 0)
            additional_costs = float(self.additional_costs_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości kosztów")
            return

        # Get selected thumbnail based on source
        thumbnail_100 = None
        preview_4k = None
        primary_source = self.graphic_source_var.get() if self.graphic_source_var.get() else None

        if primary_source == "2D" and self.frame_2d.thumbnail_data:
            thumbnail_100 = self.frame_2d.thumbnail_data
        elif primary_source == "3D" and self.frame_3d.thumbnail_data:
            thumbnail_100 = self.frame_3d.thumbnail_data
        elif primary_source == "USER" and self.frame_user.thumbnail_data:
            thumbnail_100 = self.frame_user.thumbnail_data

        # Build part data
        self.part_data = {
            'idx_code': self.idx_entry.get().strip() if self.part_data_original else '',
            'name': name,
            'material_id': material_id,
            'material_name': self.material_selector.selected_material_name,
            'thickness_mm': thickness,
            'bending_cost': bending_cost,
            'additional_costs': additional_costs,
            'cad_2d_file': self.frame_2d.file_path,
            'cad_3d_file': self.frame_3d.file_path,
            'user_image_file': self.frame_user.file_path,
            'primary_graphic_source': primary_source,
            'thumbnail_100': thumbnail_100,
            'preview_4k': preview_4k
        }

        # Save to database if needed
        if self.part_data_original and self.part_data_original.get('id'):
            # Update existing part
            self.update_part_in_db()
        elif self.order_id:
            # Create new part in order
            self.create_part_in_db()
        else:
            # Save to products_catalog
            self.save_to_catalog()

        self.destroy()

    def update_part_in_db(self):
        """Update existing part in database"""
        try:
            updates = {
                'name': self.part_data['name'],
                'material_id': self.part_data['material_id'],
                'thickness_mm': self.part_data['thickness_mm'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'cad_2d_file': self.part_data['cad_2d_file'],
                'cad_3d_file': self.part_data['cad_3d_file'],
                'user_image_file': self.part_data['user_image_file'],
                'primary_graphic_source': self.part_data['primary_graphic_source']
            }

            # Add thumbnail if available
            if self.part_data['thumbnail_100']:
                updates['thumbnail_100'] = self.part_data['thumbnail_100']

            self.db.update_part(self.part_data_original['id'], updates)
            messagebox.showinfo("Sukces", "Detal został zaktualizowany")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zaktualizować detalu:\n{e}")

    def create_part_in_db(self):
        """Create new part in database"""
        try:
            new_part_data = {
                'order_id': self.order_id,
                'name': self.part_data['name'],
                'material_id': self.part_data['material_id'],
                'thickness_mm': self.part_data['thickness_mm'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'idx_code': self.idx_entry.get().strip() if self.idx_entry.get().strip() else None,
                'cad_2d_file': self.part_data['cad_2d_file'],
                'cad_3d_file': self.part_data['cad_3d_file'],
                'user_image_file': self.part_data['user_image_file'],
                'primary_graphic_source': self.part_data['primary_graphic_source']
            }

            # Add thumbnail if available
            if self.part_data['thumbnail_100']:
                new_part_data['thumbnail_100'] = self.part_data['thumbnail_100']

            response = self.db.client.table('parts').insert(new_part_data).execute()
            if response.data:
                messagebox.showinfo("Sukces", "Detal został dodany do bazy danych")
                self.part_data.update(response.data[0])
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można dodać detalu do bazy:\n{e}")

    def save_to_catalog(self):
        """Save to products_catalog as standalone product"""
        try:
            customer_id = None
            if hasattr(self, 'customer_combo') and self.customer_combo.get():
                customer_name = self.customer_combo.get()
                if customer_name != 'Bez klienta' and hasattr(self, 'customer_map'):
                    customer_id = self.customer_map.get(customer_name)

            new_product_data = {
                'name': self.part_data['name'],
                'material_id': self.part_data['material_id'],
                'thickness_mm': self.part_data['thickness_mm'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'idx_code': self.idx_entry.get().strip() if self.idx_entry.get().strip() else None,
                'customer_id': customer_id,
                'cad_2d_file': self.part_data['cad_2d_file'],
                'cad_3d_file': self.part_data['cad_3d_file'],
                'user_image_file': self.part_data['user_image_file'],
                'primary_graphic_source': self.part_data['primary_graphic_source'],
                'description': '',
                'notes': ''
            }

            # Add thumbnail if available
            if self.part_data['thumbnail_100']:
                new_product_data['thumbnail_100'] = self.part_data['thumbnail_100']

            try:
                response = self.db.client.table('products_catalog').insert(new_product_data).execute()
                if response.data:
                    messagebox.showinfo("Sukces", "Produkt został dodany do katalogu produktów")
                    self.part_data.update(response.data[0])
                    self.part_data['_source'] = 'catalog'
            except Exception as catalog_error:
                if 'products_catalog' in str(catalog_error):
                    messagebox.showwarning(
                        "Uwaga",
                        "Tabela katalogu produktów nie istnieje w bazie danych.\n\n"
                        "Wykonaj skrypt SQL: add_products_catalog_table.sql\n"
                        "w panelu Supabase SQL Editor.\n\n"
                        "Produkt zostanie zachowany lokalnie."
                    )
                else:
                    messagebox.showerror("Błąd", f"Nie można dodać produktu:\n{catalog_error}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas zapisywania produktu:\n{e}")


def test_dialog():
    """Test dialog"""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from database import Database

    root = ctk.CTk()
    root.withdraw()

    db = Database()
    dialog = EnhancedPartEditDialogV2(root, db, [], part_data=None, order_id=None)
    root.mainloop()


if __name__ == "__main__":
    test_dialog()