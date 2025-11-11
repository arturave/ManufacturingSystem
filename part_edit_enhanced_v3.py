#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Part Edit Dialog V3 - z poprawioną integracją binarnego zapisu plików
"""

import os
import tempfile
import base64
from pathlib import Path
from typing import Optional, Dict, List, Any
from tkinter import messagebox, filedialog
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import io

# Import systemu podglądu V3
from integrated_viewer_v3 import (
    EnhancedFilePreviewFrame,
    ThumbnailGenerator
)

from image_processing import ImageProcessor
from materials_dict_module import MaterialSelector


class EnhancedPartEditDialogV3(ctk.CTkToplevel):
    """Enhanced dialog V3 z binarnym zapisem plików"""

    def __init__(self, parent, db, parts_list, part_data=None, part_index=None, order_id=None):
        super().__init__(parent)
        self.db = db
        self.parts_list = parts_list
        self.part_data_original = part_data
        self.part_index = part_index
        self.order_id = order_id

        # Zmienne dla radio buttons
        self.graphic_source_var = tk.StringVar(value="")

        # Store references to prevent garbage collection
        self.photo_references = []

        self.title("Edycja detalu V3" if part_data else "Nowy detal V3")
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

        # === KOSZTY ===
        ctk.CTkLabel(
            left_frame,
            text="💰 Koszty",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        # Material + Laser cost (main field - required)
        ctk.CTkLabel(left_frame, text="Koszt cięcia i materiał [PLN]*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.material_laser_cost_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.material_laser_cost_entry.pack(pady=5, anchor="w")
        self.material_laser_cost_entry.bind('<KeyRelease>', self.update_total_cost)

        # Bending cost
        ctk.CTkLabel(left_frame, text="Koszt gięcia [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.bending_cost_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.bending_cost_entry.pack(pady=5, anchor="w")
        self.bending_cost_entry.bind('<KeyRelease>', self.update_total_cost)

        # Additional costs
        ctk.CTkLabel(left_frame, text="Koszty dodatkowe [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.additional_costs_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.additional_costs_entry.pack(pady=5, anchor="w")
        self.additional_costs_entry.bind('<KeyRelease>', self.update_total_cost)

        # Total cost display
        total_frame = ctk.CTkFrame(left_frame, fg_color="#2b2b2b", corner_radius=8)
        total_frame.pack(pady=10, anchor="w", fill="x", padx=5)

        ctk.CTkLabel(
            total_frame,
            text="Suma kosztów:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=8)

        self.total_cost_label = ctk.CTkLabel(
            total_frame,
            text="0.00 PLN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4CAF50"
        )
        self.total_cost_label.pack(side="right", padx=10, pady=8)

        # Optional detailed costs
        ctk.CTkLabel(
            left_frame,
            text="Szczegółowe koszty (opcjonalne):",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#888888"
        ).pack(anchor="w", pady=(10, 2))

        # Material cost (optional)
        ctk.CTkLabel(left_frame, text="Koszt materiału [PLN]:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)
        self.material_cost_entry = ctk.CTkEntry(left_frame, width=200, height=30, placeholder_text="opcjonalne")
        self.material_cost_entry.pack(pady=2, anchor="w")

        # Laser cost (optional)
        ctk.CTkLabel(left_frame, text="Koszt cięcia [PLN]:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)
        self.laser_cost_entry = ctk.CTkEntry(left_frame, width=200, height=30, placeholder_text="opcjonalne")
        self.laser_cost_entry.pack(pady=2, anchor="w")

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

    def update_total_cost(self, event=None):
        """Aktualizuj wyświetlaną sumę kosztów"""
        try:
            material_laser = float(self.material_laser_cost_entry.get() or 0)
            bending = float(self.bending_cost_entry.get() or 0)
            additional = float(self.additional_costs_entry.get() or 0)

            total = material_laser + bending + additional

            self.total_cost_label.configure(text=f"{total:.2f} PLN")
        except ValueError:
            self.total_cost_label.configure(text="---.-- PLN")

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
        if self.part_data_original.get('material_laser_cost'):
            self.material_laser_cost_entry.insert(0, str(self.part_data_original['material_laser_cost']))
        if self.part_data_original.get('bending_cost'):
            self.bending_cost_entry.insert(0, str(self.part_data_original['bending_cost']))
        if self.part_data_original.get('additional_costs'):
            self.additional_costs_entry.insert(0, str(self.part_data_original['additional_costs']))
        if self.part_data_original.get('material_cost'):
            self.material_cost_entry.insert(0, str(self.part_data_original['material_cost']))
        if self.part_data_original.get('laser_cost'):
            self.laser_cost_entry.insert(0, str(self.part_data_original['laser_cost']))

        # Update total cost display
        self.update_total_cost()

        # Graphics source
        if self.part_data_original.get('primary_graphic_source'):
            self.graphic_source_var.set(self.part_data_original['primary_graphic_source'])

        # Load binary files from database
        # 2D CAD
        if self.part_data_original.get('cad_2d_binary'):
            file_binary = self.part_data_original['cad_2d_binary']
            file_name = self.part_data_original.get('cad_2d_filename', 'file.dxf')
            # Jeśli dane są zakodowane w base64 (z bazy), zdekoduj
            if isinstance(file_binary, str):
                file_binary = base64.b64decode(file_binary)
            self.frame_2d.set_file_data(file_binary, file_name)

        # 3D CAD
        if self.part_data_original.get('cad_3d_binary'):
            file_binary = self.part_data_original['cad_3d_binary']
            file_name = self.part_data_original.get('cad_3d_filename', 'file.step')
            if isinstance(file_binary, str):
                file_binary = base64.b64decode(file_binary)
            self.frame_3d.set_file_data(file_binary, file_name)

        # User image
        if self.part_data_original.get('user_image_binary'):
            file_binary = self.part_data_original['user_image_binary']
            file_name = self.part_data_original.get('user_image_filename', 'image.jpg')
            if isinstance(file_binary, str):
                file_binary = base64.b64decode(file_binary)
            self.frame_user.set_file_data(file_binary, file_name)

        # Display thumbnail if exists
        if self.part_data_original.get('thumbnail_100'):
            self.display_thumbnail(self.part_data_original['thumbnail_100'])

    def display_thumbnail(self, thumbnail_data):
        """Display thumbnail based on selected source"""
        try:
            # Decode if base64
            if isinstance(thumbnail_data, str):
                thumbnail_data = base64.b64decode(thumbnail_data)

            # Display in appropriate frame
            source = self.graphic_source_var.get()
            frame = None
            if source == "2D":
                frame = self.frame_2d
            elif source == "3D":
                frame = self.frame_3d
            elif source == "USER":
                frame = self.frame_user

            if frame:
                img = Image.open(io.BytesIO(thumbnail_data))
                photo = ImageTk.PhotoImage(img)
                frame.preview_label.configure(image=photo, text="")
                frame.preview_label.image = photo
        except Exception as e:
            print(f"Error displaying thumbnail: {e}")

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

        # Get costs - validate material_laser_cost (required)
        try:
            material_laser_cost = float(self.material_laser_cost_entry.get().strip() or 0)
            if material_laser_cost <= 0:
                messagebox.showerror("Błąd", "Koszt cięcia i materiału jest wymagany i musi być większy od 0")
                return
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowa wartość kosztu cięcia i materiału")
            return

        try:
            bending_cost = float(self.bending_cost_entry.get().strip() or 0)
            additional_costs = float(self.additional_costs_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości kosztów")
            return

        # Get optional detailed costs
        material_cost = None
        laser_cost = None
        try:
            if self.material_cost_entry.get().strip():
                material_cost = float(self.material_cost_entry.get().strip())
            if self.laser_cost_entry.get().strip():
                laser_cost = float(self.laser_cost_entry.get().strip())
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowe wartości szczegółowych kosztów")
            return

        # Get selected thumbnail based on source
        thumbnail_100 = None
        primary_source = self.graphic_source_var.get() if self.graphic_source_var.get() else None

        if primary_source == "2D" and self.frame_2d.get_thumbnail():
            thumbnail_100 = self.frame_2d.get_thumbnail()
        elif primary_source == "3D" and self.frame_3d.get_thumbnail():
            thumbnail_100 = self.frame_3d.get_thumbnail()
        elif primary_source == "USER" and self.frame_user.get_thumbnail():
            thumbnail_100 = self.frame_user.get_thumbnail()

        # Build part data
        self.part_data = {
            'idx_code': self.idx_entry.get().strip() if self.part_data_original else '',
            'name': name,
            'material_id': material_id,
            'material_name': self.material_selector.selected_material_name,
            'thickness_mm': thickness,
            'material_laser_cost': material_laser_cost,
            'bending_cost': bending_cost,
            'additional_costs': additional_costs,
            'material_cost': material_cost,
            'laser_cost': laser_cost,
            'primary_graphic_source': primary_source,
            'thumbnail_100': thumbnail_100,
            # Binary files
            'cad_2d_binary': self.frame_2d.get_file_binary(),
            'cad_2d_filename': self.frame_2d.get_file_name(),
            'cad_3d_binary': self.frame_3d.get_file_binary(),
            'cad_3d_filename': self.frame_3d.get_file_name(),
            'user_image_binary': self.frame_user.get_file_binary(),
            'user_image_filename': self.frame_user.get_file_name(),
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
                'material_laser_cost': self.part_data['material_laser_cost'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'material_cost': self.part_data['material_cost'],
                'laser_cost': self.part_data['laser_cost'],
                'primary_graphic_source': self.part_data['primary_graphic_source']
            }

            # Add binary files
            if self.part_data['cad_2d_binary']:
                updates['cad_2d_binary'] = base64.b64encode(self.part_data['cad_2d_binary']).decode('utf-8')
                updates['cad_2d_filename'] = self.part_data['cad_2d_filename']

            if self.part_data['cad_3d_binary']:
                updates['cad_3d_binary'] = base64.b64encode(self.part_data['cad_3d_binary']).decode('utf-8')
                updates['cad_3d_filename'] = self.part_data['cad_3d_filename']

            if self.part_data['user_image_binary']:
                updates['user_image_binary'] = base64.b64encode(self.part_data['user_image_binary']).decode('utf-8')
                updates['user_image_filename'] = self.part_data['user_image_filename']

            # Add thumbnail if available
            if self.part_data['thumbnail_100']:
                if isinstance(self.part_data['thumbnail_100'], bytes):
                    updates['thumbnail_100'] = base64.b64encode(self.part_data['thumbnail_100']).decode('utf-8')
                else:
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
                'material_laser_cost': self.part_data['material_laser_cost'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'material_cost': self.part_data['material_cost'],
                'laser_cost': self.part_data['laser_cost'],
                'idx_code': self.idx_entry.get().strip() if self.idx_entry.get().strip() else None,
                'primary_graphic_source': self.part_data['primary_graphic_source']
            }

            # Add binary files
            if self.part_data['cad_2d_binary']:
                new_part_data['cad_2d_binary'] = base64.b64encode(self.part_data['cad_2d_binary']).decode('utf-8')
                new_part_data['cad_2d_filename'] = self.part_data['cad_2d_filename']

            if self.part_data['cad_3d_binary']:
                new_part_data['cad_3d_binary'] = base64.b64encode(self.part_data['cad_3d_binary']).decode('utf-8')
                new_part_data['cad_3d_filename'] = self.part_data['cad_3d_filename']

            if self.part_data['user_image_binary']:
                new_part_data['user_image_binary'] = base64.b64encode(self.part_data['user_image_binary']).decode('utf-8')
                new_part_data['user_image_filename'] = self.part_data['user_image_filename']

            # Add thumbnail
            if self.part_data['thumbnail_100']:
                if isinstance(self.part_data['thumbnail_100'], bytes):
                    new_part_data['thumbnail_100'] = base64.b64encode(self.part_data['thumbnail_100']).decode('utf-8')
                else:
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
                'material_laser_cost': self.part_data['material_laser_cost'],
                'bending_cost': self.part_data['bending_cost'],
                'additional_costs': self.part_data['additional_costs'],
                'material_cost': self.part_data['material_cost'],
                'laser_cost': self.part_data['laser_cost'],
                'idx_code': self.idx_entry.get().strip() if self.idx_entry.get().strip() else None,
                'customer_id': customer_id,
                'primary_graphic_source': self.part_data['primary_graphic_source'],
                'description': '',
                'notes': ''
            }

            # Add binary files
            if self.part_data['cad_2d_binary']:
                new_product_data['cad_2d_binary'] = base64.b64encode(self.part_data['cad_2d_binary']).decode('utf-8')
                new_product_data['cad_2d_filename'] = self.part_data['cad_2d_filename']

            if self.part_data['cad_3d_binary']:
                new_product_data['cad_3d_binary'] = base64.b64encode(self.part_data['cad_3d_binary']).decode('utf-8')
                new_product_data['cad_3d_filename'] = self.part_data['cad_3d_filename']

            if self.part_data['user_image_binary']:
                new_product_data['user_image_binary'] = base64.b64encode(self.part_data['user_image_binary']).decode('utf-8')
                new_product_data['user_image_filename'] = self.part_data['user_image_filename']

            # Add thumbnail
            if self.part_data['thumbnail_100']:
                if isinstance(self.part_data['thumbnail_100'], bytes):
                    new_product_data['thumbnail_100'] = base64.b64encode(self.part_data['thumbnail_100']).decode('utf-8')
                else:
                    new_product_data['thumbnail_100'] = self.part_data['thumbnail_100']

            try:
                response = self.db.client.table('products_catalog').insert(new_product_data).execute()
                if response.data:
                    messagebox.showinfo("Sukces", "Produkt został dodany do katalogu produktów")
                    self.part_data.update(response.data[0])
                    self.part_data['_source'] = 'catalog'
            except Exception as catalog_error:
                error_msg = str(catalog_error).lower()
                if 'column' in error_msg and 'binary' in error_msg:
                    messagebox.showwarning(
                        "Uwaga",
                        "Brakuje kolumn binarnych w tabeli products_catalog.\n\n"
                        "Wykonaj skrypt SQL: 02_CLEANUP_DATABASE.sql\n"
                        "w panelu Supabase SQL Editor aby dodać kolumny binarne."
                    )
                else:
                    messagebox.showerror("Błąd", f"Nie można dodać produktu:\n{catalog_error}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas zapisywania produktu:\n{e}")


# Alias dla kompatybilności
EnhancedPartEditDialog = EnhancedPartEditDialogV3


def test_dialog():
    """Test dialog"""
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from database import Database

    root = ctk.CTk()
    root.withdraw()

    db = Database()
    dialog = EnhancedPartEditDialogV3(root, db, [], part_data=None, order_id=None)
    root.mainloop()


if __name__ == "__main__":
    test_dialog()