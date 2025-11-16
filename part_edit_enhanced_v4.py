#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Part Edit Dialog V4 - z obsługą katalogu produktów i binarnego przechowywania
"""

import os
import io
import tempfile
import base64
from pathlib import Path
from typing import Optional, Dict, List, Any
from tkinter import messagebox, filedialog
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk

# Import systemu podglądu
try:
    from integrated_viewer_v2 import (
        EnhancedFilePreviewFrame,
        ThumbnailGenerator,
        ViewerPopup
    )
except:
    # Fallback if integrated viewer is not available
    from integrated_viewer import (
        EnhancedFilePreviewFrame,
        ThumbnailGenerator,
        ViewerPopup
    )

from image_processing import ImageProcessor, get_cached_image
from materials_dict_module import MaterialSelector


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
        print(f"No data provided for {field_name}")
        return None

    try:
        # If it's already bytes, return as is
        if isinstance(data, bytes):
            print(f"{field_name}: Already bytes, length={len(data)}")
            return data

        # If it's a bytearray or memoryview (from PostgreSQL bytea), convert to bytes
        if isinstance(data, (bytearray, memoryview)):
            result = bytes(data)
            print(f"{field_name}: Converted from {type(data).__name__} to bytes, length={len(result)}")
            return result

        # If it's a string, determine format and decode
        if isinstance(data, str):
            print(f"{field_name}: String data, length={len(data)}")

            # STEP 1: Handle hex encoding (Supabase returns bytea as hex with \x prefix)
            decoded_data = data
            if data.startswith('\\x'):
                print(f"{field_name}: Detected hex format with \\x prefix")
                # Remove the \x prefix and convert from hex
                hex_str = data[2:]  # Remove '\x' prefix
                decoded_data = bytes.fromhex(hex_str)
                print(f"{field_name}: Decoded hex to {len(decoded_data)} bytes")

                # STEP 2: Check if the result is base64 encoded
                # (Our data is double-encoded: binary -> base64 -> hex)
                try:
                    # Check if decoded hex looks like base64 (all printable ASCII)
                    if all(32 <= b < 127 for b in decoded_data[:min(100, len(decoded_data))]):
                        decoded_str = decoded_data.decode('ascii')
                        print(f"{field_name}: Hex-decoded data looks like base64, attempting second decode")

                        # Try base64 decode
                        import re
                        if re.match(r'^[A-Za-z0-9+/\r\n]+=*$', decoded_str[:1000]):  # Check first 1000 chars
                            fixed_base64 = fix_base64_padding(decoded_str)
                            result = base64.b64decode(fixed_base64)
                            print(f"{field_name}: Successfully decoded base64 to {len(result)} bytes")

                            # Verify the result looks correct
                            if field_name.endswith('_binary'):
                                print(f"{field_name}: Final decoded first 20 bytes: {result[:20]}")

                            return result
                except Exception as e:
                    print(f"{field_name}: Base64 second decode failed, using hex-decoded data: {e}")

                # If not base64, return the hex-decoded data
                return decoded_data

            # First check if all chars are hex (excluding \x prefix)
            elif all(c in '0123456789ABCDEFabcdef' for c in data):
                print(f"{field_name}: All chars are hex, trying hex decode")
                try:
                    result = bytes.fromhex(data)
                    print(f"{field_name}: Decoded plain hex to {len(result)} bytes")
                    return result
                except Exception as e:
                    print(f"{field_name}: Plain hex decode failed: {e}")

            # Check if it looks like base64
            import re
            if re.match(r'^[A-Za-z0-9+/]+=*$', data):
                print(f"{field_name}: Looks like base64, attempting decode")
                try:
                    # Try to fix padding and decode as base64
                    fixed_base64 = fix_base64_padding(data)
                    result = base64.b64decode(fixed_base64)
                    print(f"{field_name}: Decoded base64 to {len(result)} bytes")
                    return result
                except Exception as e:
                    print(f"{field_name}: Base64 decode failed: {e}")

            # If nothing worked, data format is unknown
            print(f"{field_name}: Unknown data format, cannot decode")
            return None

    except Exception as e:
        print(f"Error decoding {field_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    return None


class EnhancedPartEditDialogV4(ctk.CTkToplevel):
    """Enhanced dialog V4 z obsługą katalogu produktów i trybu podglądu"""

    def __init__(self, parent, db, parts_list, part_data=None, part_index=None,
                 order_id=None, catalog_mode=False, view_only=False, title=None):
        super().__init__(parent)
        self.db = db
        self.parts_list = parts_list
        self.part_data_original = part_data
        self.part_index = part_index
        self.order_id = order_id
        self.catalog_mode = catalog_mode  # True when working with products_catalog
        self.view_only = view_only  # True for view-only mode

        # File data (binary)
        self.cad_2d_binary = None
        self.cad_3d_binary = None
        self.user_image_binary = None
        self.additional_doc_binary = None

        # File metadata
        self.cad_2d_filename = None
        self.cad_3d_filename = None
        self.user_image_filename = None
        self.additional_doc_filename = None

        # Thumbnails
        self.thumbnail_data = None
        self.preview_800_data = None
        self.preview_4k_data = None

        # Zmienne dla radio buttons
        self.graphic_source_var = tk.StringVar(value="")

        # Store references to prevent garbage collection
        self.photo_references = []

        # Set window title
        if title:
            self.title(title)
        elif view_only:
            self.title("Szczegóły produktu")
        elif catalog_mode:
            self.title("Edycja produktu w katalogu" if part_data else "Nowy produkt do katalogu")
        else:
            self.title("Edycja detalu" if part_data else "Nowy detal")

        self.geometry("1300x750")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Load existing data if editing
        if part_data:
            self.load_part_data()

        # Disable editing in view-only mode
        if self.view_only:
            self.disable_editing()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 650
        y = (self.winfo_screenheight() // 2) - 375
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components with enhanced features"""
        # Create main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Form fields
        left_frame = ctk.CTkScrollableFrame(main_container, width=450)
        left_frame.pack(side="left", fill="y", padx=5)

        # Title
        title_text = "📦 Dane produktu" if self.catalog_mode else "📝 Dane detalu"
        if self.view_only:
            title_text = "🔍 " + title_text

        ctk.CTkLabel(
            left_frame,
            text=title_text,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=10)

        # Index field (auto-generated)
        ctk.CTkLabel(left_frame, text="Indeks:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.idx_entry = ctk.CTkEntry(left_frame, width=350, height=35, state="disabled")
        self.idx_entry.pack(pady=5)

        # Customer field (for catalog products)
        if self.catalog_mode or not self.order_id:
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
        ctk.CTkLabel(left_frame, text="Nazwa*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
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

        # Category field (for catalog)
        if self.catalog_mode:
            ctk.CTkLabel(left_frame, text="Kategoria:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
            self.category_entry = ctk.CTkEntry(left_frame, width=350, height=35,
                                             placeholder_text="np. Blachy, Profile, Elementy gięte")
            self.category_entry.pack(pady=5)

            # Description field
            ctk.CTkLabel(left_frame, text="Opis:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
            self.description_text = ctk.CTkTextbox(left_frame, width=350, height=80)
            self.description_text.pack(pady=5)

        # Info about qty
        if not self.catalog_mode:
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

        # === PARAMETRY FIZYCZNE ===
        if self.catalog_mode:
            ctk.CTkLabel(
                left_frame,
                text="📐 Parametry fizyczne",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(anchor="w", pady=(10, 5))

            # Dimensions frame
            dims_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
            dims_frame.pack(fill="x", pady=5)

            # Width
            width_frame = ctk.CTkFrame(dims_frame, fg_color="transparent")
            width_frame.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(width_frame, text="Szer. [mm]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.width_entry = ctk.CTkEntry(width_frame, width=100, height=30, placeholder_text="0.0")
            self.width_entry.pack()

            # Height
            height_frame = ctk.CTkFrame(dims_frame, fg_color="transparent")
            height_frame.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(height_frame, text="Wys. [mm]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.height_entry = ctk.CTkEntry(height_frame, width=100, height=30, placeholder_text="0.0")
            self.height_entry.pack()

            # Length
            length_frame = ctk.CTkFrame(dims_frame, fg_color="transparent")
            length_frame.pack(side="left")
            ctk.CTkLabel(length_frame, text="Dł. [mm]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.length_entry = ctk.CTkEntry(length_frame, width=100, height=30, placeholder_text="0.0")
            self.length_entry.pack()

            # Weight and surface area
            phys_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
            phys_frame.pack(fill="x", pady=5)

            # Weight
            weight_frame = ctk.CTkFrame(phys_frame, fg_color="transparent")
            weight_frame.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(weight_frame, text="Waga [kg]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.weight_entry = ctk.CTkEntry(weight_frame, width=100, height=30, placeholder_text="0.000")
            self.weight_entry.pack()

            # Surface area
            surface_frame = ctk.CTkFrame(phys_frame, fg_color="transparent")
            surface_frame.pack(side="left")
            ctk.CTkLabel(surface_frame, text="Pow. [m²]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.surface_entry = ctk.CTkEntry(surface_frame, width=100, height=30, placeholder_text="0.0000")
            self.surface_entry.pack()

            # Production time and machine type
            prod_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
            prod_frame.pack(fill="x", pady=5)

            # Production time
            time_frame = ctk.CTkFrame(prod_frame, fg_color="transparent")
            time_frame.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(time_frame, text="Czas prod. [min]:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.prod_time_entry = ctk.CTkEntry(time_frame, width=100, height=30, placeholder_text="0")
            self.prod_time_entry.pack()

            # Machine type
            machine_frame = ctk.CTkFrame(prod_frame, fg_color="transparent")
            machine_frame.pack(side="left")
            ctk.CTkLabel(machine_frame, text="Typ maszyny:", font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.machine_type_entry = ctk.CTkEntry(machine_frame, width=150, height=30, placeholder_text="np. Laser CO2")
            self.machine_type_entry.pack()

        # Notes field
        ctk.CTkLabel(left_frame, text="Uwagi:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.notes_text = ctk.CTkTextbox(left_frame, width=350, height=60)
        self.notes_text.pack(pady=5)

        # Right side - Graphics previews and documentation
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Title
        ctk.CTkLabel(
            right_frame,
            text="🖼️ Pliki i dokumentacja",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        # Tabview for different file types
        self.tabview = ctk.CTkTabview(right_frame, width=700)
        self.tabview.pack(fill="both", expand=True)

        # CAD Files tab
        self.tabview.add("Pliki CAD")
        cad_tab = self.tabview.tab("Pliki CAD")

        # Preview frames for CAD
        preview_container = ctk.CTkFrame(cad_tab)
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

        # Add download button for 2D - always visible
        self.add_download_button(self.frame_2d, "cad_2d")

        # 3D CAD Preview
        self.frame_3d = EnhancedFilePreviewFrame(
            preview_container,
            "Plik 3D (STEP/STL)",
            ['.step', '.stp', '.iges', '.igs', '.stl'],
            self.graphic_source_var,
            "3D"
        )
        self.frame_3d.pack(side="left", padx=10, fill="y")

        # Add download button for 3D - always visible
        self.add_download_button(self.frame_3d, "cad_3d")

        # Grafika tab
        self.tabview.add("Grafika")
        graphics_tab = self.tabview.tab("Grafika")

        graphics_container = ctk.CTkFrame(graphics_tab)
        graphics_container.pack(fill="both", expand=True, padx=10, pady=10)

        # User Image Preview
        self.frame_user = EnhancedFilePreviewFrame(
            graphics_container,
            "Grafika użytkownika",
            ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
            self.graphic_source_var,
            "USER"
        )
        self.frame_user.pack(side="left", padx=10, fill="y")

        # Add download button for user image - always visible
        self.add_download_button(self.frame_user, "user_image")

        # Generated thumbnails preview
        thumb_frame = ctk.CTkFrame(graphics_container)
        thumb_frame.pack(side="left", padx=10, fill="y")

        ctk.CTkLabel(thumb_frame, text="Wygenerowane miniatury",
                    font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.thumbnail_label = ctk.CTkLabel(thumb_frame, text="", width=200, height=150)
        self.thumbnail_label.pack(pady=5)

        ctk.CTkLabel(thumb_frame, text="Miniatura 100x100",
                    font=ctk.CTkFont(size=10)).pack()

        # Add download buttons for thumbnails - always visible
        thumb_download_frame = ctk.CTkFrame(thumb_frame)
        thumb_download_frame.pack(pady=10)

        self.download_thumb_button = ctk.CTkButton(
            thumb_download_frame,
            text="💾 Miniatura",
            width=120,
            height=28,
            command=lambda: self.download_thumbnail("thumbnail_100")
        )
        self.download_thumb_button.pack(pady=2)

        self.download_preview_button = ctk.CTkButton(
            thumb_download_frame,
            text="💾 Podgląd 800px",
            width=120,
            height=28,
            command=lambda: self.download_thumbnail("preview_800")
        )
        self.download_preview_button.pack(pady=2)

        self.download_4k_button = ctk.CTkButton(
            thumb_download_frame,
            text="💾 Podgląd 4K",
            width=120,
            height=28,
            command=lambda: self.download_thumbnail("preview_4k")
        )
        self.download_4k_button.pack(pady=2)

        # Documentation tab
        self.tabview.add("Dokumentacja")
        docs_tab = self.tabview.tab("Dokumentacja")

        docs_container = ctk.CTkFrame(docs_tab)
        docs_container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            docs_container,
            text="📄 Dodatkowa dokumentacja",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=10)

        ctk.CTkLabel(
            docs_container,
            text="Możesz dodać archiwum ZIP lub 7Z z dokumentacją techniczną",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        ).pack(anchor="w", pady=5)

        # Documentation file info
        self.doc_info_frame = ctk.CTkFrame(docs_container, fg_color="#2b2b2b")
        self.doc_info_frame.pack(fill="x", pady=10)

        self.doc_info_label = ctk.CTkLabel(
            self.doc_info_frame,
            text="Brak dokumentacji",
            font=ctk.CTkFont(size=12)
        )
        self.doc_info_label.pack(pady=10)

        # Documentation buttons
        doc_btn_frame = ctk.CTkFrame(docs_container, fg_color="transparent")
        doc_btn_frame.pack(fill="x", pady=5)

        self.doc_load_btn = ctk.CTkButton(
            doc_btn_frame,
            text="📁 Wybierz archiwum",
            width=150,
            command=self.load_documentation
        )
        self.doc_load_btn.pack(side="left", padx=5)

        self.doc_clear_btn = ctk.CTkButton(
            doc_btn_frame,
            text="❌ Usuń",
            width=100,
            command=self.clear_documentation,
            fg_color="#666666"
        )
        self.doc_clear_btn.pack(side="left", padx=5)

        # Add download button for documentation - always visible
        self.doc_download_btn = ctk.CTkButton(
            doc_btn_frame,
            text="💾 Pobierz",
            width=100,
            command=self.download_documentation
        )
        self.doc_download_btn.pack(side="left", padx=5)

        # Info about selected graphic source
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
                # Automatycznie generuj miniatury przy zmianie źródła
                self.generate_and_update_thumbnails()
            else:
                info_label.configure(text="⚠️ Wybierz źródło grafiki")

        self.graphic_source_var.trace('w', update_source_info)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", side="bottom", padx=10, pady=10)

        if not self.view_only:
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
        else:
            ctk.CTkButton(
                button_frame,
                text="Zamknij",
                width=150,
                command=self.destroy
            ).pack(side="right", padx=5)

    def load_documentation(self):
        """Load additional documentation archive"""
        file_path = filedialog.askopenfilename(
            title="Wybierz archiwum z dokumentacją",
            filetypes=[
                ("Archiwa", "*.zip;*.7z"),
                ("ZIP", "*.zip"),
                ("7Z", "*.7z"),
                ("Wszystkie", "*.*")
            ]
        )

        if file_path:
            try:
                # Read file as binary
                with open(file_path, 'rb') as f:
                    self.additional_doc_binary = f.read()

                self.additional_doc_filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)

                # Update UI
                self.doc_info_label.configure(
                    text=f"📦 {self.additional_doc_filename}\n"
                         f"Rozmiar: {file_size / 1024 / 1024:.2f} MB"
                )

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można wczytać dokumentacji:\n{e}")

    def clear_documentation(self):
        """Clear loaded documentation"""
        self.additional_doc_binary = None
        self.additional_doc_filename = None
        self.doc_info_label.configure(text="Brak dokumentacji")

    def update_total_cost(self, event=None):
        """Update displayed total cost"""
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

        print("\n" + "="*60)
        print("DEBUG: load_part_data START")
        print(f"DEBUG: part_data_original keys: {list(self.part_data_original.keys())}")
        print("\nDEBUG: URL fields in part_data_original:")
        print(f"  - cad_2d_url: {self.part_data_original.get('cad_2d_url', 'NOT FOUND')}")
        print(f"  - cad_3d_url: {self.part_data_original.get('cad_3d_url', 'NOT FOUND')}")
        print(f"  - user_image_url: {self.part_data_original.get('user_image_url', 'NOT FOUND')}")
        print(f"  - thumbnail_100_url: {self.part_data_original.get('thumbnail_100_url', 'NOT FOUND')}")
        print("="*60 + "\n")

        # Basic fields
        self.idx_entry.configure(state="normal")
        self.idx_entry.insert(0, self.part_data_original.get('idx_code') or '')
        self.idx_entry.configure(state="disabled")

        self.name_entry.insert(0, self.part_data_original.get('name') or '')

        # Customer (for catalog mode)
        if self.catalog_mode or not self.order_id:
            if self.part_data_original.get('customer_id'):
                # Find customer name
                for name, cid in self.customer_map.items():
                    if cid == self.part_data_original.get('customer_id'):
                        self.customer_combo.set(name)
                        break

        # Material
        if self.part_data_original.get('material_id'):
            self.material_selector.set_material(self.part_data_original['material_id'])

        # Thickness
        if self.part_data_original.get('thickness_mm'):
            self.thickness_entry.insert(0, str(self.part_data_original['thickness_mm']))

        # Category and description (for catalog)
        if self.catalog_mode:
            if hasattr(self, 'category_entry') and self.part_data_original.get('category'):
                self.category_entry.insert(0, self.part_data_original['category'] or '')

            if hasattr(self, 'description_text') and self.part_data_original.get('description'):
                self.description_text.insert("1.0", self.part_data_original['description'] or '')

            # Physical parameters
            if hasattr(self, 'width_entry') and self.part_data_original.get('width_mm'):
                self.width_entry.insert(0, str(self.part_data_original['width_mm']))

            if hasattr(self, 'height_entry') and self.part_data_original.get('height_mm'):
                self.height_entry.insert(0, str(self.part_data_original['height_mm']))

            if hasattr(self, 'length_entry') and self.part_data_original.get('length_mm'):
                self.length_entry.insert(0, str(self.part_data_original['length_mm']))

            if hasattr(self, 'weight_entry') and self.part_data_original.get('weight_kg'):
                self.weight_entry.insert(0, str(self.part_data_original['weight_kg']))

            if hasattr(self, 'surface_entry') and self.part_data_original.get('surface_area_m2'):
                self.surface_entry.insert(0, str(self.part_data_original['surface_area_m2']))

            if hasattr(self, 'prod_time_entry') and self.part_data_original.get('production_time_minutes'):
                self.prod_time_entry.insert(0, str(self.part_data_original['production_time_minutes']))

            if hasattr(self, 'machine_type_entry') and self.part_data_original.get('machine_type'):
                self.machine_type_entry.insert(0, self.part_data_original['machine_type'])

        # Costs
        if self.part_data_original.get('material_laser_cost'):
            self.material_laser_cost_entry.insert(0, str(self.part_data_original['material_laser_cost']))

        if self.part_data_original.get('bending_cost'):
            self.bending_cost_entry.insert(0, str(self.part_data_original['bending_cost']))

        if self.part_data_original.get('additional_costs'):
            self.additional_costs_entry.insert(0, str(self.part_data_original['additional_costs']))

        # Notes
        if self.part_data_original.get('notes'):
            self.notes_text.insert("1.0", self.part_data_original['notes'] or '')

        # Load files - try URL first, then fallback to binary
        # CAD 2D
        if self.part_data_original.get('cad_2d_url'):
            print(f"\n=== Loading CAD 2D from URL ===")
            print(f"URL: {self.part_data_original['cad_2d_url']}")
            try:
                import requests
                response = requests.get(self.part_data_original['cad_2d_url'], timeout=10)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                if response.status_code == 200:
                    self.cad_2d_binary = response.content
                    self.cad_2d_filename = self.part_data_original.get('cad_2d_filename', 'file.dxf')
                    print(f"Downloaded {len(self.cad_2d_binary)} bytes")
                    print(f"First 100 bytes: {self.cad_2d_binary[:100]}")
                    self.load_binary_to_preview(self.cad_2d_binary, self.cad_2d_filename, self.frame_2d)
                else:
                    print(f"Failed to download: HTTP {response.status_code}")
                    print(f"Response text: {response.text[:500]}")
            except Exception as e:
                print(f"Error downloading CAD 2D: {e}")
                import traceback
                traceback.print_exc()
        elif self.part_data_original.get('cad_2d_binary'):
            # Fallback to legacy bytea
            print(f"\n=== Loading CAD 2D Binary (legacy) ===")
            raw_data = self.part_data_original['cad_2d_binary']
            if raw_data:  # Check if not None
                print(f"Raw data type: {type(raw_data)}")
                if isinstance(raw_data, str):
                    print(f"Raw data length: {len(raw_data)} chars")

                self.cad_2d_binary = safe_decode_binary(
                    raw_data,
                    field_name='cad_2d_binary'
                )

                if self.cad_2d_binary:
                    print(f"Decoded to {len(self.cad_2d_binary)} bytes")
                    self.cad_2d_filename = self.part_data_original.get('cad_2d_filename', 'file.dxf')
                    self.load_binary_to_preview(self.cad_2d_binary, self.cad_2d_filename, self.frame_2d)
                else:
                    print("Failed to decode CAD 2D binary")

        # CAD 3D
        if self.part_data_original.get('cad_3d_url'):
            print(f"\n=== Loading CAD 3D from URL ===")
            print(f"URL: {self.part_data_original['cad_3d_url']}")
            try:
                import requests
                response = requests.get(self.part_data_original['cad_3d_url'], timeout=10)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                if response.status_code == 200:
                    self.cad_3d_binary = response.content
                    self.cad_3d_filename = self.part_data_original.get('cad_3d_filename', 'file.stp')
                    print(f"Downloaded {len(self.cad_3d_binary)} bytes")
                    print(f"First 100 bytes: {self.cad_3d_binary[:100]}")
                    print(f"Calling load_binary_to_preview with frame_3d...")
                    self.load_binary_to_preview(self.cad_3d_binary, self.cad_3d_filename, self.frame_3d)
                else:
                    print(f"Failed to download: HTTP {response.status_code}")
                    print(f"Response text: {response.text[:500]}")
            except Exception as e:
                print(f"Error downloading CAD 3D: {e}")
                import traceback
                traceback.print_exc()
        elif self.part_data_original.get('cad_3d_binary'):
            print(f"\n=== Loading CAD 3D Binary (legacy) ===")
            raw_data = self.part_data_original['cad_3d_binary']
            if raw_data:  # Check if not None
                print(f"Raw data type: {type(raw_data)}")
                if isinstance(raw_data, str):
                    print(f"Raw data length: {len(raw_data)} chars")

                self.cad_3d_binary = safe_decode_binary(
                    raw_data,
                    field_name='cad_3d_binary'
                )
                if self.cad_3d_binary:
                    print(f"Decoded to {len(self.cad_3d_binary)} bytes")
                    self.cad_3d_filename = self.part_data_original.get('cad_3d_filename', 'file.stp')
                    self.load_binary_to_preview(self.cad_3d_binary, self.cad_3d_filename, self.frame_3d)
                else:
                    print("Failed to decode CAD 3D binary")

        # User Image
        if self.part_data_original.get('user_image_url'):
            print(f"\n=== Loading User Image from URL ===")
            print(f"URL: {self.part_data_original['user_image_url']}")
            try:
                import requests
                response = requests.get(self.part_data_original['user_image_url'], timeout=10)
                if response.status_code == 200:
                    self.user_image_binary = response.content
                    self.user_image_filename = self.part_data_original.get('user_image_filename', 'image.png')
                    print(f"Downloaded {len(self.user_image_binary)} bytes")
                    self.load_binary_to_preview(self.user_image_binary, self.user_image_filename, self.frame_user)
                else:
                    print(f"Failed to download: HTTP {response.status_code}")
            except Exception as e:
                print(f"Error downloading User Image: {e}")
        elif self.part_data_original.get('user_image_binary'):
            print(f"\n=== Loading User Image Binary (legacy) ===")
            raw_data = self.part_data_original['user_image_binary']
            if raw_data:  # Check if not None
                print(f"Raw data type: {type(raw_data)}")
                if isinstance(raw_data, str):
                    print(f"Raw data length: {len(raw_data)} chars")

                self.user_image_binary = safe_decode_binary(
                    raw_data,
                    field_name='user_image_binary'
                )
                if self.user_image_binary:
                    print(f"Decoded to {len(self.user_image_binary)} bytes")
                    self.user_image_filename = self.part_data_original.get('user_image_filename', 'image.png')
                    self.load_binary_to_preview(self.user_image_binary, self.user_image_filename, self.frame_user)
                else:
                    print("Failed to decode user image binary")

        # Load documentation
        if self.part_data_original.get('additional_documentation_url'):
            print(f"\n=== Loading Documentation from URL ===")
            print(f"URL: {self.part_data_original['additional_documentation_url']}")
            try:
                import requests
                response = requests.get(self.part_data_original['additional_documentation_url'], timeout=30)
                if response.status_code == 200:
                    self.additional_doc_binary = response.content
                    self.additional_doc_filename = self.part_data_original.get('additional_documentation_filename', 'docs.zip')
                    print(f"Downloaded {len(self.additional_doc_binary)} bytes")
                    # Update doc info label
                    file_size = len(self.additional_doc_binary)
                    self.doc_info_label.configure(
                        text=f"📦 {self.additional_doc_filename}\n"
                             f"Rozmiar: {file_size / 1024 / 1024:.2f} MB"
                    )
                else:
                    print(f"Failed to download: HTTP {response.status_code}")
            except Exception as e:
                print(f"Error downloading documentation: {e}")
        elif self.part_data_original.get('additional_documentation'):
            self.additional_doc_binary = safe_decode_binary(
                self.part_data_original['additional_documentation'],
                field_name='additional_documentation'
            )
            if self.additional_doc_binary:
                self.additional_doc_filename = self.part_data_original.get('additional_documentation_filename', 'docs.zip')
                file_size = len(self.additional_doc_binary)
                self.doc_info_label.configure(
                    text=f"📦 {self.additional_doc_filename}\n"
                         f"Rozmiar: {file_size / 1024 / 1024:.2f} MB"
                )
                # Show download button if in view mode
                if self.view_only and hasattr(self, 'doc_download_btn'):
                    self.doc_download_btn.pack(side="left", padx=5)

        # Load thumbnail if exists - try URL first, then bytea
        if self.part_data_original.get('thumbnail_100_url'):
            try:
                print(f"\n=== Loading thumbnail from URL ===")
                print(f"URL: {self.part_data_original['thumbnail_100_url']}")
                import requests
                response = requests.get(self.part_data_original['thumbnail_100_url'], timeout=5)
                if response.status_code == 200:
                    self.display_thumbnail(response.content)
                    print(f"Thumbnail loaded from URL")
            except Exception as e:
                print(f"Failed to load thumbnail from URL: {e}")
        elif self.part_data_original.get('thumbnail_100'):
            try:
                # Legacy bytea
                if self.part_data_original['thumbnail_100']:
                    self.display_thumbnail(self.part_data_original['thumbnail_100'])
            except:
                pass

        # Set graphic source
        if self.part_data_original.get('primary_graphic_source'):
            self.graphic_source_var.set(self.part_data_original['primary_graphic_source'])

        # Update total cost
        self.update_total_cost()

    def load_binary_to_preview(self, binary_data, filename, preview_frame):
        """Load binary data to preview frame via temporary file"""
        print(f"\n=== load_binary_to_preview START ===")
        print(f"Filename: {filename}")
        print(f"Preview frame: {preview_frame}")
        print(f"Preview frame type: {type(preview_frame)}")

        if not binary_data:
            print("No binary data provided, returning")
            return

        try:
            print(f"Loading binary data for {filename}")
            print(f"Binary data type: {type(binary_data)}")
            print(f"Binary data length: {len(binary_data) if binary_data else 0}")

            # Ensure we have bytes
            if not isinstance(binary_data, bytes):
                print(f"Warning: binary_data is not bytes, it's {type(binary_data)}")
                return

            # Verify data looks correct
            if filename.lower().endswith('.dxf'):
                # DXF files should start with ASCII text like "0\nSECTION"
                header = binary_data[:100]
                print(f"DXF header (first 100 bytes): {header[:100]}")

            elif filename.lower().endswith('.png'):
                # PNG files should start with PNG signature
                if binary_data[:8] != b'\x89PNG\r\n\x1a\n':
                    print(f"Warning: PNG signature not found. Got: {binary_data[:8].hex()}")
                else:
                    print("PNG signature verified")

            elif filename.lower().endswith(('.stp', '.step')):
                # STEP files should start with "ISO-10303-21"
                header = binary_data[:100]
                print(f"STEP header: {header[:100]}")

            # Create temporary file
            suffix = Path(filename).suffix
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(binary_data)
                temp_path = tmp.name
                print(f"Wrote {len(binary_data)} bytes to temp file: {temp_path}")

            # Verify temp file was created
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"Temp file exists: {temp_path}, size: {file_size} bytes")
            else:
                print(f"ERROR: Temp file not found after creation: {temp_path}")

            # Set file path in preview frame
            print(f"Setting preview_frame.file_path to: {temp_path}")
            preview_frame.file_path = temp_path
            print(f"Preview frame now has file_path: {hasattr(preview_frame, 'file_path')}")

            # Update label
            print(f"Setting file_label text to: {Path(filename).name}")
            if hasattr(preview_frame, 'file_label'):
                preview_frame.file_label.configure(text=Path(filename).name)
                print(f"Label updated successfully")
            else:
                print(f"WARNING: preview_frame has no file_label attribute")

            # Enable preview button
            print(f"Enabling preview button")
            if hasattr(preview_frame, 'preview_button'):
                preview_frame.preview_button.configure(state="normal")
                print(f"Preview button enabled")
            else:
                print(f"WARNING: preview_frame has no preview_button attribute")

            print(f"=== load_binary_to_preview SUCCESS ===\n")

            # Mark file as loaded
            preview_frame.file_loaded = True

            # Update button states if they exist (not all preview frames have these buttons)
            if hasattr(preview_frame, 'load_button'):
                preview_frame.load_button.configure(text="✓ Załadowano")
            if hasattr(preview_frame, 'clear_button'):
                preview_frame.clear_button.configure(state="normal")

            # Generate and display thumbnail
            if hasattr(preview_frame, 'generate_and_display_thumbnail'):
                print(f"Calling generate_and_display_thumbnail for {filename}")
                try:
                    preview_frame.generate_and_display_thumbnail()
                    print(f"Thumbnail generation completed")

                    # If this is the selected source, also update the main thumbnail preview
                    if hasattr(preview_frame, 'radio_value') and preview_frame.radio_value == self.graphic_source_var.get():
                        self.generate_and_update_thumbnails()
                        print(f"Updated main thumbnail preview for selected source: {preview_frame.radio_value}")
                except Exception as e:
                    print(f"Error generating thumbnail: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"WARNING: preview_frame has no generate_and_display_thumbnail method")

            print(f"Successfully loaded {filename} to preview frame")

            # Store reference to clean up later
            if not hasattr(self, '_temp_files'):
                self._temp_files = []
            self._temp_files.append(temp_path)

        except Exception as e:
            print(f"Error loading binary to preview: {e}")
            import traceback
            traceback.print_exc()

    def display_thumbnail(self, thumbnail_data):
        """Display thumbnail in UI"""
        try:
            # Use safe_decode_binary for consistent handling
            img_data = safe_decode_binary(thumbnail_data, field_name='thumbnail')

            # If still no data and it's a hex string, try hex decoding
            if not img_data and isinstance(thumbnail_data, str):
                if thumbnail_data.startswith('\\x'):
                    try:
                        hex_str = thumbnail_data.replace('\\x', '')
                        img_data = bytes.fromhex(hex_str)
                    except:
                        return

            if not img_data:
                return

            img = Image.open(io.BytesIO(img_data))

            # Resize for display
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.thumbnail_label.configure(image=photo)
            self.thumbnail_label.image = photo  # Keep reference

        except Exception as e:
            print(f"Error displaying thumbnail: {e}")

    def disable_editing(self):
        """Disable all editing controls for view-only mode"""
        # Disable all entry fields
        self.name_entry.configure(state="disabled")
        self.thickness_entry.configure(state="disabled")
        self.material_laser_cost_entry.configure(state="disabled")
        self.bending_cost_entry.configure(state="disabled")
        self.additional_costs_entry.configure(state="disabled")

        if hasattr(self, 'customer_combo'):
            self.customer_combo.configure(state="disabled")

        if hasattr(self, 'category_entry'):
            self.category_entry.configure(state="disabled")

        if hasattr(self, 'description_text'):
            self.description_text.configure(state="disabled")

        self.notes_text.configure(state="disabled")

        # Disable material selector
        if hasattr(self.material_selector, 'material_combo'):
            self.material_selector.material_combo.configure(state="disabled")

        # Disable file loading buttons
        for frame in [self.frame_2d, self.frame_3d, self.frame_user]:
            if hasattr(frame, 'load_btn'):
                frame.load_btn.configure(state="disabled")
            if hasattr(frame, 'clear_btn'):
                frame.clear_btn.configure(state="disabled")

        self.doc_load_btn.configure(state="disabled")
        self.doc_clear_btn.configure(state="disabled")

    def save_part(self):
        """Save part data with binary file storage"""
        # Validate required fields
        if not self.name_entry.get():
            messagebox.showerror("Błąd", "Nazwa jest wymagana!")
            return

        if not self.material_selector.get_selected_material_id():
            messagebox.showerror("Błąd", "Materiał jest wymagany!")
            return

        if not self.thickness_entry.get():
            messagebox.showerror("Błąd", "Grubość jest wymagana!")
            return

        try:
            # Prepare part data
            self.part_data = {
                'name': self.name_entry.get(),
                'material_id': self.material_selector.get_selected_material_id(),
                'thickness_mm': float(self.thickness_entry.get()),
                'material_laser_cost': float(self.material_laser_cost_entry.get() or 0),
                'bending_cost': float(self.bending_cost_entry.get() or 0),
                'additional_costs': float(self.additional_costs_entry.get() or 0),
                'notes': self.notes_text.get("1.0", "end-1c"),
                'primary_graphic_source': self.graphic_source_var.get() or None
            }

            # Add catalog-specific fields
            if self.catalog_mode:
                if hasattr(self, 'customer_combo'):
                    customer_name = self.customer_combo.get()
                    if customer_name != 'Bez klienta':
                        self.part_data['customer_id'] = self.customer_map.get(customer_name)

                if hasattr(self, 'category_entry'):
                    self.part_data['category'] = self.category_entry.get() or None

                if hasattr(self, 'description_text'):
                    self.part_data['description'] = self.description_text.get("1.0", "end-1c")

                # Physical parameters
                if hasattr(self, 'width_entry') and self.width_entry.get():
                    try:
                        self.part_data['width_mm'] = float(self.width_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'height_entry') and self.height_entry.get():
                    try:
                        self.part_data['height_mm'] = float(self.height_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'length_entry') and self.length_entry.get():
                    try:
                        self.part_data['length_mm'] = float(self.length_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'weight_entry') and self.weight_entry.get():
                    try:
                        self.part_data['weight_kg'] = float(self.weight_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'surface_entry') and self.surface_entry.get():
                    try:
                        self.part_data['surface_area_m2'] = float(self.surface_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'prod_time_entry') and self.prod_time_entry.get():
                    try:
                        self.part_data['production_time_minutes'] = int(self.prod_time_entry.get())
                    except ValueError:
                        pass

                if hasattr(self, 'machine_type_entry') and self.machine_type_entry.get():
                    self.part_data['machine_type'] = self.machine_type_entry.get()

            # Get files from preview frames and convert to binary
            if hasattr(self.frame_2d, 'file_path') and self.frame_2d.file_path:
                try:
                    with open(self.frame_2d.file_path, 'rb') as f:
                        self.part_data['cad_2d_binary'] = f.read()
                        self.part_data['cad_2d_filename'] = os.path.basename(self.frame_2d.file_path)
                except Exception as e:
                    print(f"Error reading 2D file: {e}")

            if hasattr(self.frame_3d, 'file_path') and self.frame_3d.file_path:
                try:
                    with open(self.frame_3d.file_path, 'rb') as f:
                        self.part_data['cad_3d_binary'] = f.read()
                        self.part_data['cad_3d_filename'] = os.path.basename(self.frame_3d.file_path)
                except Exception as e:
                    print(f"Error reading 3D file: {e}")

            if hasattr(self.frame_user, 'file_path') and self.frame_user.file_path:
                try:
                    with open(self.frame_user.file_path, 'rb') as f:
                        self.part_data['user_image_binary'] = f.read()
                        self.part_data['user_image_filename'] = os.path.basename(self.frame_user.file_path)
                except Exception as e:
                    print(f"Error reading user image: {e}")

            # Add documentation
            if self.additional_doc_binary:
                self.part_data['additional_documentation'] = self.additional_doc_binary
                self.part_data['additional_documentation_filename'] = self.additional_doc_filename

            # Generate thumbnails
            self.generate_thumbnails()

            # Add thumbnails to part data
            if self.thumbnail_data:
                self.part_data['thumbnail_100'] = self.thumbnail_data
            if self.preview_800_data:
                self.part_data['preview_800'] = self.preview_800_data
            if self.preview_4k_data:
                self.part_data['preview_4k'] = self.preview_4k_data

            # Close dialog
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Błąd", f"Nieprawidłowe dane: {e}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać danych: {e}")

    def generate_and_update_thumbnails(self):
        """Generate thumbnails and update UI immediately"""
        source = self.graphic_source_var.get()

        if not source:
            print("No graphic source selected for thumbnail generation")
            # Clear thumbnail display
            self.thumbnail_label.configure(image="", text="Brak miniatury")
            return

        # Generate thumbnails
        self.generate_thumbnails()

        # Update thumbnail display immediately
        if self.thumbnail_data:
            self.display_thumbnail_in_preview(self.thumbnail_data)

    def display_thumbnail_in_preview(self, thumbnail_data):
        """Display thumbnail in the preview section"""
        try:
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(thumbnail_data))

            # Scale to fit the preview label
            img.thumbnail((200, 150), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Update the label
            self.thumbnail_label.configure(image=photo, text="")
            self.thumbnail_label.image = photo  # Keep reference

            print(f"Thumbnail displayed in preview section")
        except Exception as e:
            print(f"Error displaying thumbnail in preview: {e}")
            self.thumbnail_label.configure(image="", text="Błąd wyświetlania")

    def generate_thumbnails(self):
        """Generate thumbnails from selected graphic source"""
        source = self.graphic_source_var.get()

        if not source:
            print("No graphic source selected for thumbnail generation")
            return

        try:
            # Check if ThumbnailGenerator is available
            if not ThumbnailGenerator:
                print("ThumbnailGenerator not available")
                return

            file_path = None

            # Get file path based on source
            if source == "2D" and hasattr(self.frame_2d, 'file_path'):
                file_path = self.frame_2d.file_path
                print(f"Using 2D file for thumbnail: {file_path}")
            elif source == "3D" and hasattr(self.frame_3d, 'file_path'):
                file_path = self.frame_3d.file_path
                print(f"Using 3D file for thumbnail: {file_path}")
            elif source == "USER" and hasattr(self.frame_user, 'file_path'):
                file_path = self.frame_user.file_path
                print(f"Using USER image for thumbnail: {file_path}")

            if file_path and os.path.exists(file_path):
                print(f"Generating thumbnails from: {file_path}")
                try:
                    # Use proper static methods based on source type
                    if source == "2D":
                        self.thumbnail_data = ThumbnailGenerator.generate_from_2d_cad(file_path, (100, 100))
                        self.preview_800_data = ThumbnailGenerator.generate_from_2d_cad(file_path, (800, 800))
                        self.preview_4k_data = ThumbnailGenerator.generate_from_2d_cad(file_path, (3840, 2160))
                    elif source == "3D":
                        self.thumbnail_data = ThumbnailGenerator.generate_from_3d_cad(file_path, (100, 100))
                        self.preview_800_data = ThumbnailGenerator.generate_from_3d_cad(file_path, (800, 800))
                        self.preview_4k_data = ThumbnailGenerator.generate_from_3d_cad(file_path, (3840, 2160))
                    elif source == "USER":
                        self.thumbnail_data = ThumbnailGenerator.generate_from_image(file_path, (100, 100))
                        self.preview_800_data = ThumbnailGenerator.generate_from_image(file_path, (800, 800))
                        self.preview_4k_data = ThumbnailGenerator.generate_from_image(file_path, (3840, 2160))

                    print(f"Generated thumbnail_100: {len(self.thumbnail_data) if self.thumbnail_data else 0} bytes")
                    print(f"Generated preview_800: {len(self.preview_800_data) if self.preview_800_data else 0} bytes")
                    print(f"Generated preview_4k: {len(self.preview_4k_data) if self.preview_4k_data else 0} bytes")

                except Exception as e:
                    print(f"Error generating thumbnails: {e}")
                    import traceback
                    traceback.print_exc()

                # Display generated thumbnail
                if self.thumbnail_data:
                    self.display_thumbnail(self.thumbnail_data)
            else:
                print(f"File path not found or doesn't exist: {file_path}")

        except Exception as e:
            print(f"Error in generate_thumbnails: {e}")
            import traceback
            traceback.print_exc()

    def add_download_button(self, preview_frame, file_type):
        """Add download button to preview frame"""
        download_btn = ctk.CTkButton(
            preview_frame,
            text="💾 Pobierz",
            width=100,
            height=28,
            command=lambda: self.download_file(file_type)
        )
        download_btn.pack(pady=5)

    def download_file(self, file_type):
        """Download file to user's computer"""
        try:
            # Get binary data and filename based on type
            if file_type == "cad_2d":
                binary_data = self.cad_2d_binary if hasattr(self, 'cad_2d_binary') else None
                default_name = self.cad_2d_filename if hasattr(self, 'cad_2d_filename') else "file.dxf"
            elif file_type == "cad_3d":
                binary_data = self.cad_3d_binary if hasattr(self, 'cad_3d_binary') else None
                default_name = self.cad_3d_filename if hasattr(self, 'cad_3d_filename') else "file.stp"
            elif file_type == "user_image":
                binary_data = self.user_image_binary if hasattr(self, 'user_image_binary') else None
                default_name = self.user_image_filename if hasattr(self, 'user_image_filename') else "image.png"
            else:
                messagebox.showwarning("Błąd", f"Nieznany typ pliku: {file_type}")
                return

            if not binary_data:
                messagebox.showinfo("Info", "Brak pliku do pobrania")
                return

            # Ask user where to save
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=Path(default_name).suffix,
                initialfile=default_name,
                filetypes=[
                    ("All files", "*.*"),
                    (f"{Path(default_name).suffix.upper()} files", f"*{Path(default_name).suffix}")
                ]
            )

            if file_path:
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(binary_data)
                messagebox.showinfo("Sukces", f"Plik zapisany: {file_path}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać pliku: {str(e)}")

    def download_thumbnail(self, thumb_type):
        """Download thumbnail/preview image"""
        try:
            # Get thumbnail data based on type
            if thumb_type == "thumbnail_100":
                binary_data = self.thumbnail_data if hasattr(self, 'thumbnail_data') else None
                default_name = f"{self.name_entry.get()}_thumbnail_100.jpg"
            elif thumb_type == "preview_800":
                binary_data = self.preview_800_data if hasattr(self, 'preview_800_data') else None
                default_name = f"{self.name_entry.get()}_preview_800.jpg"
            elif thumb_type == "preview_4k":
                binary_data = self.preview_4k_data if hasattr(self, 'preview_4k_data') else None
                default_name = f"{self.name_entry.get()}_preview_4k.jpg"
            else:
                return

            if not binary_data:
                # Try to get from original data
                if thumb_type == "thumbnail_100" and self.part_data_original.get('thumbnail_100'):
                    binary_data = safe_decode_binary(self.part_data_original['thumbnail_100'])
                elif thumb_type == "preview_800" and self.part_data_original.get('preview_800'):
                    binary_data = safe_decode_binary(self.part_data_original['preview_800'])
                elif thumb_type == "preview_4k" and self.part_data_original.get('preview_4k'):
                    binary_data = safe_decode_binary(self.part_data_original['preview_4k'])

            if not binary_data:
                messagebox.showinfo("Info", f"Brak {thumb_type.replace('_', ' ')} do pobrania")
                return

            # Ask user where to save
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                initialfile=default_name,
                filetypes=[
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(binary_data)
                messagebox.showinfo("Sukces", f"Obraz zapisany: {file_path}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać obrazu: {str(e)}")

    def download_documentation(self):
        """Download documentation archive"""
        try:
            if not hasattr(self, 'additional_doc_binary') or not self.additional_doc_binary:
                messagebox.showinfo("Info", "Brak dokumentacji do pobrania")
                return

            default_name = self.additional_doc_filename if hasattr(self, 'additional_doc_filename') else "documentation.zip"

            # Ask user where to save
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=Path(default_name).suffix,
                initialfile=default_name,
                filetypes=[
                    ("Archive files", "*.zip *.7z"),
                    ("ZIP files", "*.zip"),
                    ("7Z files", "*.7z"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(self.additional_doc_binary)
                messagebox.showinfo("Sukces", f"Dokumentacja zapisana: {file_path}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać dokumentacji: {str(e)}")

    def __del__(self):
        """Clean up temporary files"""
        if hasattr(self, '_temp_files'):
            for temp_file in self._temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass