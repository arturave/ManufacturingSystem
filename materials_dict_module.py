#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Materials Dictionary Module
Manages materials dictionary with categories and properties
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List, Dict, Any


class MaterialsDictDialog(ctk.CTkToplevel):
    """Dialog for managing materials dictionary"""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db

        self.title("Słownik materiałów")
        self.geometry("1000x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.load_materials()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 500
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="📋 Słownik materiałów",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=10)

        # Buttons
        btn_frame = ctk.CTkFrame(header)
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="➕ Dodaj",
            width=100,
            command=self.add_material
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="✏️ Edytuj",
            width=100,
            command=self.edit_material
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Usuń",
            width=100,
            command=self.delete_material,
            fg_color="#d32f2f"
        ).pack(side="left", padx=5)

        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Filtruj:").pack(side="left", padx=5)

        self.filter_entry = ctk.CTkEntry(filter_frame, width=200, placeholder_text="Nazwa materiału...")
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self.filter_materials())

        self.category_var = ctk.StringVar(value="Wszystkie")
        self.category_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Wszystkie", "STAL", "STAL_NIERDZEWNA", "ALUMINIUM", "MOSIADZ", "MIEDZ", "STAL_SPECJALNA"],
            variable=self.category_var,
            command=lambda x: self.filter_materials(),
            width=200
        )
        self.category_combo.pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="🔄 Odśwież",
            width=100,
            command=self.load_materials
        ).pack(side="right", padx=5)

        # Materials list (using frame with scrollbar)
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create scrollable frame
        self.materials_scroll = ctk.CTkScrollableFrame(list_frame)
        self.materials_scroll.pack(fill="both", expand=True)

        # Headers
        headers_frame = ctk.CTkFrame(self.materials_scroll)
        headers_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(headers_frame, text="Nazwa", width=250, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Kategoria", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Gęstość [g/cm³]", width=120, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Opis", width=300, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Status", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        # Materials container
        self.materials_container = ctk.CTkFrame(self.materials_scroll)
        self.materials_container.pack(fill="both", expand=True)

        # Store materials data
        self.materials_data = []
        self.selected_material_id = None

    def load_materials(self):
        """Load materials from database"""
        try:
            response = self.db.client.table('materials_dict').select("*").order('name').execute()
            self.materials_data = response.data
            self.display_materials(self.materials_data)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować materiałów:\n{e}")

    def display_materials(self, materials: List[Dict]):
        """Display materials in the list"""
        # Clear existing widgets
        for widget in self.materials_container.winfo_children():
            widget.destroy()

        # Display each material
        for material in materials:
            self.create_material_row(material)

    def create_material_row(self, material: Dict):
        """Create a row for a material"""
        row = ctk.CTkFrame(self.materials_container)
        row.pack(fill="x", pady=2)

        # Make row clickable
        row.bind("<Button-1>", lambda e, m=material: self.select_material(m))

        # Name
        name_label = ctk.CTkLabel(row, text=material['name'], width=250, anchor="w")
        name_label.pack(side="left", padx=5)
        name_label.bind("<Button-1>", lambda e, m=material: self.select_material(m))

        # Category
        category_label = ctk.CTkLabel(row, text=material.get('category', '-'), width=150, anchor="w")
        category_label.pack(side="left", padx=5)
        category_label.bind("<Button-1>", lambda e, m=material: self.select_material(m))

        # Density
        density_text = f"{material.get('density', '-')}" if material.get('density') else "-"
        density_label = ctk.CTkLabel(row, text=density_text, width=120, anchor="w")
        density_label.pack(side="left", padx=5)
        density_label.bind("<Button-1>", lambda e, m=material: self.select_material(m))

        # Description
        desc_text = material.get('description', '-')[:50] + "..." if len(material.get('description', '')) > 50 else material.get('description', '-')
        desc_label = ctk.CTkLabel(row, text=desc_text, width=300, anchor="w")
        desc_label.pack(side="left", padx=5)
        desc_label.bind("<Button-1>", lambda e, m=material: self.select_material(m))

        # Active status
        status_text = "Aktywny" if material.get('is_active', True) else "Nieaktywny"
        status_color = "#4caf50" if material.get('is_active', True) else "#ff9800"
        status_label = ctk.CTkLabel(row, text=status_text, width=80, text_color=status_color)
        status_label.pack(side="left", padx=5)
        status_label.bind("<Button-1>", lambda e, m=material: self.select_material(m))

    def select_material(self, material: Dict):
        """Select a material"""
        self.selected_material_id = material['id']
        # Highlight selected row (simple approach - reload with selection)
        self.display_materials(self.materials_data)

    def filter_materials(self):
        """Filter materials based on search criteria"""
        search_text = self.filter_entry.get().lower()
        category = self.category_var.get()

        filtered = []
        for material in self.materials_data:
            # Check name filter
            if search_text and search_text not in material['name'].lower():
                continue

            # Check category filter
            if category != "Wszystkie" and material.get('category') != category:
                continue

            filtered.append(material)

        self.display_materials(filtered)

    def add_material(self):
        """Add new material"""
        dialog = MaterialEditDialog(self, self.db, None)
        self.wait_window(dialog)

        if hasattr(dialog, 'result') and dialog.result:
            self.load_materials()

    def edit_material(self):
        """Edit selected material"""
        if not self.selected_material_id:
            messagebox.showwarning("Uwaga", "Wybierz materiał do edycji")
            return

        # Find material data
        material = next((m for m in self.materials_data if m['id'] == self.selected_material_id), None)
        if not material:
            messagebox.showwarning("Uwaga", "Nie znaleziono wybranego materiału")
            return

        dialog = MaterialEditDialog(self, self.db, material)
        self.wait_window(dialog)

        if hasattr(dialog, 'result') and dialog.result:
            self.load_materials()

    def delete_material(self):
        """Delete selected material"""
        if not self.selected_material_id:
            messagebox.showwarning("Uwaga", "Wybierz materiał do usunięcia")
            return

        # Find material name
        material = next((m for m in self.materials_data if m['id'] == self.selected_material_id), None)
        if not material:
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć materiał '{material['name']}'?\n\n"
            "Uwaga: Materiał nie zostanie usunięty jeśli jest używany w częściach."
        )

        if result:
            try:
                self.db.client.table('materials_dict').delete().eq('id', self.selected_material_id).execute()
                messagebox.showinfo("Sukces", "Materiał został usunięty")
                self.selected_material_id = None
                self.load_materials()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można usunąć materiału:\n{e}\n\nMożliwe, że materiał jest używany w częściach.")


class MaterialEditDialog(ctk.CTkToplevel):
    """Dialog for adding/editing material"""

    def __init__(self, parent, db, material_data: Optional[Dict] = None):
        super().__init__(parent)
        self.db = db
        self.material_data = material_data
        self.result = False

        self.title("Edycja materiału" if material_data else "Nowy materiał")
        self.geometry("600x500")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 300
        y = (self.winfo_screenheight() // 2) - 250
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Setup UI components"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Name
        ctk.CTkLabel(main_frame, text="Nazwa materiału*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=500, height=35)
        self.name_entry.pack(pady=5)

        # Category
        ctk.CTkLabel(main_frame, text="Kategoria:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.category_var = ctk.StringVar(value="STAL")
        self.category_combo = ctk.CTkComboBox(
            main_frame,
            values=["STAL", "STAL_NIERDZEWNA", "ALUMINIUM", "MOSIADZ", "MIEDZ", "STAL_SPECJALNA"],
            variable=self.category_var,
            width=500,
            height=35
        )
        self.category_combo.pack(pady=5)

        # Density
        ctk.CTkLabel(main_frame, text="Gęstość [g/cm³]:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.density_entry = ctk.CTkEntry(main_frame, width=200, height=35, placeholder_text="np. 7.85")
        self.density_entry.pack(pady=5, anchor="w")

        # Description
        ctk.CTkLabel(main_frame, text="Opis:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.description_text = ctk.CTkTextbox(main_frame, width=500, height=100)
        self.description_text.pack(pady=5)

        # Active status
        self.active_var = ctk.BooleanVar(value=True)
        self.active_check = ctk.CTkCheckBox(
            main_frame,
            text="Materiał aktywny",
            variable=self.active_var
        )
        self.active_check.pack(anchor="w", pady=10)

        # Load data if editing
        if self.material_data:
            self.name_entry.insert(0, self.material_data.get('name', ''))
            self.category_var.set(self.material_data.get('category', 'STAL'))
            if self.material_data.get('density'):
                self.density_entry.insert(0, str(self.material_data['density']))
            if self.material_data.get('description'):
                self.description_text.insert("1.0", self.material_data['description'])
            self.active_var.set(self.material_data.get('is_active', True))

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Zapisz",
            width=150,
            command=self.save_material
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            width=150,
            command=self.destroy
        ).pack(side="right", padx=10)

    def save_material(self):
        """Save material data"""
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Uwaga", "Nazwa materiału jest wymagana")
            return

        # Parse density
        density = None
        density_str = self.density_entry.get().strip()
        if density_str:
            try:
                density = float(density_str)
            except ValueError:
                messagebox.showwarning("Uwaga", "Nieprawidłowa wartość gęstości")
                return

        data = {
            'name': name,
            'category': self.category_var.get(),
            'density': density,
            'description': self.description_text.get("1.0", "end").strip() or None,
            'is_active': self.active_var.get()
        }

        try:
            if self.material_data:
                # Update existing
                self.db.client.table('materials_dict').update(data).eq('id', self.material_data['id']).execute()
                messagebox.showinfo("Sukces", "Materiał został zaktualizowany")
            else:
                # Create new
                self.db.client.table('materials_dict').insert(data).execute()
                messagebox.showinfo("Sukces", "Materiał został dodany")

            self.result = True
            self.destroy()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać materiału:\n{e}")


class MaterialSelector(ctk.CTkFrame):
    """Widget for selecting material from dictionary"""

    def __init__(self, parent, db, on_select_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db
        self.on_select_callback = on_select_callback
        self.selected_material_id = None
        self.selected_material_name = None

        self.setup_ui()
        self.load_materials()

    def setup_ui(self):
        """Setup UI components"""
        # Combo box for material selection
        self.material_var = ctk.StringVar(value="-- Wybierz materiał --")
        self.material_combo = ctk.CTkComboBox(
            self,
            variable=self.material_var,
            command=self.on_material_selected,
            width=300
        )
        self.material_combo.pack(side="left", padx=5)

        # Button to open materials dict
        ctk.CTkButton(
            self,
            text="📋",
            width=40,
            command=self.open_materials_dict
        ).pack(side="left", padx=5)

    def load_materials(self):
        """Load materials from database"""
        try:
            response = self.db.client.table('materials_dict').select("*").eq('is_active', True).order('name').execute()
            self.materials_data = response.data

            # Update combo box
            material_names = ["-- Wybierz materiał --"] + [m['name'] for m in self.materials_data]
            self.material_combo.configure(values=material_names)

        except Exception as e:
            print(f"Error loading materials: {e}")
            self.materials_data = []

    def on_material_selected(self, selected_name: str):
        """Handle material selection"""
        if selected_name == "-- Wybierz materiał --":
            self.selected_material_id = None
            self.selected_material_name = None
        else:
            # Find material by name
            material = next((m for m in self.materials_data if m['name'] == selected_name), None)
            if material:
                self.selected_material_id = material['id']
                self.selected_material_name = material['name']

                # Call callback if provided
                if self.on_select_callback:
                    self.on_select_callback(material)

    def open_materials_dict(self):
        """Open materials dictionary dialog"""
        dialog = MaterialsDictDialog(self, self.db)
        self.wait_window(dialog)

        # Reload materials after dialog closes
        self.load_materials()

    def get_selected_material_id(self) -> Optional[str]:
        """Get selected material ID"""
        return self.selected_material_id

    def set_material(self, material_id: str):
        """Set selected material by ID"""
        material = next((m for m in self.materials_data if m['id'] == material_id), None)
        if material:
            self.material_var.set(material['name'])
            self.selected_material_id = material_id
            self.selected_material_name = material['name']
