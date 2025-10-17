#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Part Edit Dialog
Includes: graphics, file upload, drag-and-drop, Ctrl+V paste, duplicate detection
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
#import ezdxf
#from ezdxf.addons.drawing import Frontend, RenderContext, svg, layout


# Try to import tkinterdnd2 for drag & drop support (optional)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False
    print("Info: tkinterdnd2 not installed. Drag & drop functionality will not be available.")
    print("      Install with: pip install tkinterdnd2")

from image_processing import ImageProcessor, get_cached_image
from cad_processing import CADProcessor
from materials_dict_module import MaterialSelector


class EnhancedPartEditDialog(ctk.CTkToplevel):
    """Enhanced dialog for adding/editing parts with graphics and advanced features"""

    def __init__(self, parent, db, parts_list, part_data=None, part_index=None, order_id=None):
        super().__init__(parent)
        self.db = db
        self.parts_list = parts_list
        self.part_data_original = part_data
        self.part_index = part_index
        self.order_id = order_id  # For duplicate detection

        # Graphics paths
        self.high_res_path = None
        self.low_res_path = None
        self.documentation_path = None
        self.current_image = None  # PIL Image

        # Duplicate detection
        self.suggested_duplicates = []

        self.title("Edycja detalu" if part_data else "Nowy detal")
        self.geometry("900x800")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.setup_drag_and_drop()
        self.setup_keyboard_shortcuts()

        # Load existing data if editing
        if part_data:
            self.load_part_data()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 450
        y = (self.winfo_screenheight() // 2) - 400
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components"""
        # Create main container with scrollable frame
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Form fields
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Index field (auto-generated)
        ctk.CTkLabel(left_frame, text="Indeks (auto):", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.idx_entry = ctk.CTkEntry(left_frame, width=400, height=35, state="disabled")
        self.idx_entry.pack(pady=5)

        # Name field
        ctk.CTkLabel(left_frame, text="Nazwa detalu*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.name_entry = ctk.CTkEntry(left_frame, width=400, height=35)
        self.name_entry.pack(pady=5)
        self.name_entry.bind("<FocusOut>", lambda e: self.check_duplicates())

        # Material selector
        ctk.CTkLabel(left_frame, text="Materiał*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.material_selector = MaterialSelector(left_frame, self.db, on_select_callback=self.check_duplicates)
        self.material_selector.pack(pady=5, anchor="w")

        # Thickness field
        ctk.CTkLabel(left_frame, text="Grubość [mm]*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.thickness_entry = ctk.CTkEntry(left_frame, width=200, height=35)
        self.thickness_entry.pack(pady=5, anchor="w")
        self.thickness_entry.bind("<FocusOut>", lambda e: self.check_duplicates())

        # Quantity field
        ctk.CTkLabel(left_frame, text="Ilość:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.qty_entry = ctk.CTkEntry(left_frame, width=200, height=35)
        self.qty_entry.pack(pady=5, anchor="w")
        self.qty_entry.insert(0, "1")

        # Bending cost
        ctk.CTkLabel(left_frame, text="Koszt gięcia [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.bending_cost_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.bending_cost_entry.pack(pady=5, anchor="w")

        # Additional costs
        ctk.CTkLabel(left_frame, text="Koszty dodatkowe [PLN]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.additional_costs_entry = ctk.CTkEntry(left_frame, width=200, height=35, placeholder_text="0.00")
        self.additional_costs_entry.pack(pady=5, anchor="w")

        # Right side - Graphics and files
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", padx=5)

        # Graphics preview
        ctk.CTkLabel(right_frame, text="Grafika:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        self.image_preview = ctk.CTkLabel(right_frame, text="", width=350, height=250)
        self.image_preview.pack(pady=5)
        self.display_placeholder()

        # File upload buttons
        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="📁 Wybierz grafikę",
            width=160,
            command=self.upload_image
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="📋 Wklej (Ctrl+V)",
            width=160,
            command=self.paste_image
        ).pack(side="left", padx=5)

        # CAD file upload
        ctk.CTkLabel(right_frame, text="Dokumentacja CAD:", font=ctk.CTkFont(size=14)).pack(pady=5)

        cad_btn_frame = ctk.CTkFrame(right_frame)
        cad_btn_frame.pack(pady=5)

        ctk.CTkButton(
            cad_btn_frame,
            text="📄 DXF/DWG",
            width=100,
            command=lambda: self.upload_cad_file(['dxf', 'dwg'])
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            cad_btn_frame,
            text="📦 3D (STEP/IGS)",
            width=120,
            command=lambda: self.upload_cad_file(['step', 'stp', 'igs', 'iges'])
        ).pack(side="left", padx=5)

        # Documentation file label
        self.doc_label = ctk.CTkLabel(right_frame, text="Brak pliku CAD", text_color="#999999")
        self.doc_label.pack(pady=5)

        # Drag and drop hint
        hint_text = "💡 Przeciągnij i upuść pliki tutaj\nlub użyj Ctrl+V dla grafiki" if TKDND_AVAILABLE else "💡 Użyj przycisków powyżej\nlub Ctrl+V dla grafiki"
        hint_label = ctk.CTkLabel(
            right_frame,
            text=hint_text,
            text_color="#666666",
            font=ctk.CTkFont(size=11)
        )
        hint_label.pack(pady=10)

        # Duplicate warning frame (initially hidden)
        self.duplicate_frame = ctk.CTkFrame(self, fg_color="#ff9800")
        self.duplicate_label = ctk.CTkLabel(
            self.duplicate_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.duplicate_label.pack(pady=10, padx=10)

        # Buttons at bottom
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkButton(
            bottom_frame,
            text="💾 Zapisz",
            width=150,
            height=40,
            command=self.save_part,
            fg_color="#4caf50"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            bottom_frame,
            text="❌ Anuluj",
            width=150,
            height=40,
            command=self.destroy
        ).pack(side="right", padx=10)

    def setup_drag_and_drop(self):
        """Setup drag and drop for files"""
        if not TKDND_AVAILABLE:
            print("Info: Drag and drop not available (tkinterdnd2 not installed)")
            return

        try:
            # Try to enable drag and drop (requires tkinterdnd2)
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
        except Exception as e:
            print(f"Drag and drop setup failed: {e}")

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.bind("<Control-v>", lambda e: self.paste_image())
        self.bind("<Control-s>", lambda e: self.save_part())

    def on_drop(self, event):
        """Handle dropped files"""
        files = self.tk.splitlist(event.data)
        if files:
            file_path = files[0]
            self.process_dropped_file(file_path)

    def process_dropped_file(self, file_path: str):
        """Process dropped file - image or CAD"""
        ext = Path(file_path).suffix.lower()

        if ImageProcessor.is_image_file(file_path):
            # Load and process image
            image = ImageProcessor.load_image_from_file(file_path)
            if image:
                self.set_image(image)
                messagebox.showinfo("Sukces", "Grafika została załadowana")
        elif CADProcessor.is_cad_file(file_path):
            # Process CAD file
            self.process_cad_file(file_path)
        else:
            messagebox.showwarning("Uwaga", f"Nieobsługiwany format pliku: {ext}")

    def upload_image(self):
        """Upload image file"""
        file_path = filedialog.askopenfilename(
            title="Wybierz grafikę",
            filetypes=[
                ("Pliki graficzne", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("Wszystkie pliki", "*.*")
            ]
        )

        if file_path:
            image = ImageProcessor.load_image_from_file(file_path)
            if image:
                self.set_image(image)
                messagebox.showinfo("Sukces", "Grafika została załadowana")
            else:
                messagebox.showerror("Błąd", "Nie można załadować grafiki")

    def paste_image(self):
        """Paste image from clipboard (Ctrl+V)"""
        image = ImageProcessor.load_image_from_clipboard()
        if image:
            self.set_image(image)
            messagebox.showinfo("Sukces", "Grafika została wklejona ze schowka")
        else:
            messagebox.showwarning("Uwaga", "Brak grafiki w schowku")

    def upload_cad_file(self, extensions: List[str]):
        """Upload CAD file"""
        filetypes = [
            ("Pliki CAD", " ".join([f"*.{ext}" for ext in extensions])),
            ("Wszystkie pliki", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Wybierz plik CAD",
            filetypes=filetypes
        )

        if file_path:
            self.process_cad_file(file_path)

    def process_cad_file(self, file_path: str):
        """Process CAD file and generate preview with both high-res and low-res versions"""
        try:
            # Store documentation path
            self.documentation_path = file_path
            self.doc_label.configure(
                text=f"📄 {Path(file_path).name}",
                text_color="#4caf50"
            )

            # Generate temporary paths for both resolutions
            temp_high_res = tempfile.NamedTemporaryFile(suffix='_high.png', delete=False)
            temp_high_res_path = temp_high_res.name
            temp_high_res.close()

            temp_low_res = tempfile.NamedTemporaryFile(suffix='_low.png', delete=False)
            temp_low_res_path = temp_low_res.name
            temp_low_res.close()

            # Process CAD file to generate both resolutions
            high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
                file_path,
                temp_high_res_path,
                temp_low_res_path
            )

            if high_success:
                # Load high-res image for preview display
                image = ImageProcessor.load_image_from_file(temp_high_res_path)
                if image:
                    self.set_image(image)

                    # Store both paths for later saving
                    self.high_res_path = temp_high_res_path
                    self.low_res_path = temp_low_res_path

                    messagebox.showinfo(
                        "Sukces",
                        f"Plik CAD został przetworzony:\n"
                        f"✓ Wysoka rozdzielczość (300 DPI)\n"
                        f"✓ Niska rozdzielczość (miniatura)\n"
                        f"✓ Podgląd wygenerowany"
                    )
                else:
                    # If image loading failed, clean up
                    try:
                        os.unlink(temp_high_res_path)
                        os.unlink(temp_low_res_path)
                    except:
                        pass
                    messagebox.showwarning("Uwaga", "Nie można załadować wygenerowanego podglądu")
            else:
                # Clean up temp files on failure
                try:
                    if os.path.exists(temp_high_res_path):
                        os.unlink(temp_high_res_path)
                    if os.path.exists(temp_low_res_path):
                        os.unlink(temp_low_res_path)
                except:
                    pass
                # Check file type for better error message
                file_type = CADProcessor.get_file_type(file_path)
                if file_type in ['step', 'iges']:
                    messagebox.showwarning(
                        "Uwaga",
                        "Nie można wygenerować podglądu z pliku 3D.\n"
                        "Sprawdź czy zainstalowano wymagane biblioteki:\n"
                        "- pythonocc-core (instalacja: conda install -c conda-forge pythonocc-core)\n"
                        "\nAlternatywnie możesz użyć grafiki PNG/JPG."
                    )
                else:
                    messagebox.showwarning(
                        "Uwaga",
                        "Nie można wygenerować podglądu z pliku CAD.\n"
                        "Sprawdź czy plik jest poprawny i czy zainstalowano wymagane biblioteki:\n"
                        "- ezdxf\n"
                        "- pymupdf"
                    )

        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd przetwarzania pliku CAD:\n{e}")
            import traceback
            traceback.print_exc()

    def set_image(self, image: Image.Image):
        """Set current image and display preview"""
        self.current_image = image

        # Determine if high-res or low-res based on size
        res_type = ImageProcessor.determine_resolution_type(image)

        # Display preview (max 350x250)
        preview_image = ImageProcessor.create_photoimage(image.copy(), (350, 250))
        self.image_preview.configure(image=preview_image, text="")
        self.image_preview.image = preview_image  # Keep reference

    def display_placeholder(self):
        """Display placeholder image"""
        placeholder = ImageProcessor.create_placeholder_image((350, 250), "Brak grafiki")
        photo = ImageTk.PhotoImage(placeholder)
        self.image_preview.configure(image=photo, text="")
        self.image_preview.image = photo

    def check_duplicates(self, *args):
        """Check for duplicate parts"""
        name = self.name_entry.get().strip()
        thickness_str = self.thickness_entry.get().strip()
        material_id = self.material_selector.get_selected_material_id()

        # Only check if we have enough info
        if not name or not thickness_str or not material_id:
            self.duplicate_frame.pack_forget()
            return

        try:
            thickness = float(thickness_str)
        except ValueError:
            self.duplicate_frame.pack_forget()
            return

        # Check for duplicates via database function
        try:
            response = self.db.client.rpc(
                'check_duplicate_parts_fn',
                {
                    'p_name': name,
                    'p_thickness': thickness,
                    'p_material_id': material_id,
                    'p_exclude_id': self.part_data_original.get('id') if self.part_data_original else None
                }
            ).execute()

            duplicates = response.data

            if duplicates and len(duplicates) > 0:
                # Show warning
                top_match = duplicates[0]
                self.duplicate_label.configure(
                    text=f"⚠️ Znaleziono podobny detal: {top_match['idx_code']} - {top_match['name']}\n"
                         f"Materiał: {top_match['material_name']}, Grubość: {top_match['thickness_mm']}mm\n"
                         f"Czy chcesz użyć istniejącego detalu?"
                )
                self.duplicate_frame.pack(fill="x", padx=10, pady=5)
                self.suggested_duplicates = duplicates
            else:
                self.duplicate_frame.pack_forget()
                self.suggested_duplicates = []

        except Exception as e:
            print(f"Error checking duplicates: {e}")
            self.duplicate_frame.pack_forget()

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
        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, str(self.part_data_original.get('qty', 1)))

        # Material
        if self.part_data_original.get('material_id'):
            self.material_selector.set_material(self.part_data_original['material_id'])

        # Costs
        if self.part_data_original.get('bending_cost'):
            self.bending_cost_entry.insert(0, str(self.part_data_original['bending_cost']))
        if self.part_data_original.get('additional_costs'):
            self.additional_costs_entry.insert(0, str(self.part_data_original['additional_costs']))

        # Graphics
        if self.part_data_original.get('graphic_high_res'):
            # TODO: Load from storage
            pass

        if self.part_data_original.get('documentation_path'):
            self.documentation_path = self.part_data_original['documentation_path']
            self.doc_label.configure(
                text=f"📄 {Path(self.documentation_path).name}",
                text_color="#4caf50"
            )

    def save_part(self):
        """Save part data"""
        # Validate
        name = self.name_entry.get().strip()
        thickness_str = self.thickness_entry.get().strip()
        material_id = self.material_selector.get_selected_material_id()

        if not name:
            messagebox.showwarning("Uwaga", "Nazwa detalu jest wymagana")
            return

        if not material_id:
            messagebox.showwarning("Uwaga", "Materiał jest wymagany")
            return

        if not thickness_str:
            messagebox.showwarning("Uwaga", "Grubość jest wymagana")
            return

        try:
            thickness = float(thickness_str)
        except ValueError:
            messagebox.showwarning("Uwaga", "Nieprawidłowa wartość grubości")
            return

        # Parse costs
        bending_cost = 0.0
        bending_cost_str = self.bending_cost_entry.get().strip()
        if bending_cost_str:
            try:
                bending_cost = float(bending_cost_str)
            except ValueError:
                messagebox.showwarning("Uwaga", "Nieprawidłowa wartość kosztu gięcia")
                return

        additional_costs = 0.0
        additional_costs_str = self.additional_costs_entry.get().strip()
        if additional_costs_str:
            try:
                additional_costs = float(additional_costs_str)
            except ValueError:
                messagebox.showwarning("Uwaga", "Nieprawidłowa wartość kosztów dodatkowych")
                return

        # Process and save images if present
        # Check if we already have high/low res paths from CAD processing
        if self.high_res_path and self.low_res_path:
            # CAD file was processed, use existing paths
            high_res_path = self.high_res_path
            low_res_path = self.low_res_path
        elif self.current_image:
            # Regular image was loaded, generate both resolutions
            temp_dir = tempfile.mkdtemp()
            high_res_path, low_res_path = ImageProcessor.process_and_save_both(
                self.current_image,
                temp_dir,
                f"part_{name}"
            )
        else:
            high_res_path = None
            low_res_path = None

        # Check for duplicate names in current parts list (exclude current part if editing)
        for i, part in enumerate(self.parts_list):
            if part['name'] == name and i != self.part_index:
                # Ask if user wants to create duplicate
                result = messagebox.askyesno(
                    "Duplikat",
                    f"Detal o nazwie '{name}' już istnieje!\n\n"
                    "Czy chcesz utworzyć duplikat?"
                )
                if not result:
                    return

        # Build part data
        self.part_data = {
            'idx_code': self.idx_entry.get().strip() if self.part_data_original else '',  # Auto-generated in DB
            'name': name,
            'material_id': material_id,
            'material_name': self.material_selector.selected_material_name,  # For display
            'thickness_mm': thickness,
            'qty': int(self.qty_entry.get().strip() or 1),
            'bending_cost': bending_cost,
            'additional_costs': additional_costs,
            'graphic_high_res': high_res_path,
            'graphic_low_res': low_res_path,
            'documentation_path': self.documentation_path
        }

        # Add to database if we have order_id (editing existing part)
        if self.part_data_original and self.part_data_original.get('id'):
            # Update existing part in database
            try:
                updates = {
                    'name': name,
                    'material_id': material_id,
                    'thickness_mm': thickness,
                    'qty': int(self.qty_entry.get().strip() or 1),
                    'bending_cost': bending_cost,
                    'additional_costs': additional_costs
                }

                # TODO: Upload graphics to Supabase Storage
                # if high_res_path:
                #     updates['graphic_high_res'] = uploaded_high_res_path
                # if low_res_path:
                #     updates['graphic_low_res'] = uploaded_low_res_path
                # if self.documentation_path:
                #     updates['documentation_path'] = uploaded_doc_path

                self.db.update_part(self.part_data_original['id'], updates)
                messagebox.showinfo("Sukces", "Detal został zaktualizowany")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zaktualizować detalu:\n{e}")
                return

        self.destroy()

    def use_suggested_duplicate(self):
        """Use suggested duplicate instead of creating new"""
        if not self.suggested_duplicates:
            return

        # Use first suggested duplicate
        duplicate = self.suggested_duplicates[0]

        result = messagebox.askyesno(
            "Użyj istniejącego detalu",
            f"Czy chcesz użyć istniejącego detalu?\n\n"
            f"Indeks: {duplicate['idx_code']}\n"
            f"Nazwa: {duplicate['name']}\n"
            f"Materiał: {duplicate['material_name']}\n"
            f"Grubość: {duplicate['thickness_mm']}mm"
        )

        if result:
            # Load duplicate data
            self.part_data = duplicate
            self.destroy()
