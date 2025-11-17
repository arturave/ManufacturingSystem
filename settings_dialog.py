#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Dialog for Manufacturing System
Provides GUI for managing application settings
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional, Callable
from pathlib import Path
from settings_manager import get_settings_manager, ApplicationSettings


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window"""

    def __init__(self, parent, callback: Optional[Callable] = None):
        """
        Initialize settings dialog

        Args:
            parent: Parent window
            callback: Optional callback to call when settings are saved
        """
        super().__init__(parent)

        self.callback = callback
        self.settings_manager = get_settings_manager()
        self.settings = self.settings_manager.settings

        # Window configuration
        self.title("Ustawienia aplikacji")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Center window
        self.transient(parent)
        self.grab_set()

        # Variables for form fields
        self.setup_variables()

        # Create UI
        self.setup_ui()

        # Load current settings
        self.load_current_settings()

        # Center window after content is loaded
        self.center_window()

    def setup_variables(self):
        """Setup tkinter variables for form fields"""
        # Company info
        self.company_name_var = tk.StringVar(value=self.settings.company_name)
        self.company_address_var = tk.StringVar(value=self.settings.company_address)
        self.company_phone_var = tk.StringVar(value=self.settings.company_phone)
        self.company_email_var = tk.StringVar(value=self.settings.company_email)
        self.company_nip_var = tk.StringVar(value=self.settings.company_nip)
        self.company_regon_var = tk.StringVar(value=self.settings.company_regon)

        # Logo settings
        self.use_user_logo_var = tk.BooleanVar(value=self.settings.use_user_logo)
        self.user_logo_path_var = tk.StringVar(value=self.settings.user_logo_path)

        # Report settings
        self.report_include_thumbnails_var = tk.BooleanVar(value=self.settings.report_include_thumbnails)
        self.report_include_details_var = tk.BooleanVar(value=self.settings.report_include_details)
        self.report_language_var = tk.StringVar(value=self.settings.report_language)

        # Display settings
        self.list_show_thumbnails_var = tk.BooleanVar(value=self.settings.list_show_thumbnails)
        self.theme_mode_var = tk.StringVar(value=self.settings.theme_mode)
        self.color_theme_var = tk.StringVar(value=self.settings.color_theme)

        # Export settings
        self.export_format_var = tk.StringVar(value=self.settings.export_format)
        self.export_include_attachments_var = tk.BooleanVar(value=self.settings.export_include_attachments)
        self.export_compress_images_var = tk.BooleanVar(value=self.settings.export_compress_images)
        self.export_image_quality_var = tk.IntVar(value=self.settings.export_image_quality)

    def setup_ui(self):
        """Setup user interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.company_tab = self.notebook.add("Dane firmy")
        self.logo_tab = self.notebook.add("Logo")
        self.report_tab = self.notebook.add("Raporty")
        self.display_tab = self.notebook.add("Wyświetlanie")
        self.export_tab = self.notebook.add("Eksport")

        # Setup each tab
        self.setup_company_tab()
        self.setup_logo_tab()
        self.setup_report_tab()
        self.setup_display_tab()
        self.setup_export_tab()

        # Buttons frame
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        # Save button
        self.save_button = ctk.CTkButton(
            button_frame,
            text="Zapisz",
            command=self.save_settings,
            width=120
        )
        self.save_button.pack(side="right", padx=5)

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Anuluj",
            command=self.destroy,
            width=120,
            fg_color="gray"
        )
        self.cancel_button.pack(side="right", padx=5)

        # Reset button
        self.reset_button = ctk.CTkButton(
            button_frame,
            text="Przywróć domyślne",
            command=self.reset_to_defaults,
            width=150,
            fg_color="orange"
        )
        self.reset_button.pack(side="left", padx=5)

    def setup_company_tab(self):
        """Setup company information tab"""
        frame = ctk.CTkScrollableFrame(self.company_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Company name
        ctk.CTkLabel(frame, text="Nazwa firmy:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.company_name_var, width=400).grid(row=0, column=1, padx=5, pady=5)

        # Address
        ctk.CTkLabel(frame, text="Adres:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        address_text = ctk.CTkTextbox(frame, width=400, height=60)
        address_text.grid(row=1, column=1, padx=5, pady=5)
        address_text.insert("1.0", self.company_address_var.get())
        self.address_textbox = address_text

        # Phone
        ctk.CTkLabel(frame, text="Telefon:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.company_phone_var, width=400).grid(row=2, column=1, padx=5, pady=5)

        # Email
        ctk.CTkLabel(frame, text="Email:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.company_email_var, width=400).grid(row=3, column=1, padx=5, pady=5)

        # NIP
        ctk.CTkLabel(frame, text="NIP:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.company_nip_var, width=400).grid(row=4, column=1, padx=5, pady=5)

        # REGON
        ctk.CTkLabel(frame, text="REGON:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(frame, textvariable=self.company_regon_var, width=400).grid(row=5, column=1, padx=5, pady=5)

    def setup_logo_tab(self):
        """Setup logo configuration tab"""
        frame = ctk.CTkFrame(self.logo_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Current logo preview
        preview_frame = ctk.CTkFrame(frame)
        preview_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(preview_frame, text="Aktualne logo:", font=("Arial", 14, "bold")).pack(pady=5)

        self.logo_preview_label = ctk.CTkLabel(preview_frame, text="")
        self.logo_preview_label.pack(pady=10)

        # Load and display current logo
        self.update_logo_preview()

        # Logo selection
        selection_frame = ctk.CTkFrame(frame)
        selection_frame.pack(fill="x", padx=10, pady=10)

        # Manufacturer logo option
        self.manufacturer_radio = ctk.CTkRadioButton(
            selection_frame,
            text="Logo producenta",
            variable=self.use_user_logo_var,
            value=False,
            command=self.on_logo_selection_changed
        )
        self.manufacturer_radio.pack(anchor="w", padx=10, pady=5)

        # User logo option
        self.user_radio = ctk.CTkRadioButton(
            selection_frame,
            text="Logo użytkownika",
            variable=self.use_user_logo_var,
            value=True,
            command=self.on_logo_selection_changed
        )
        self.user_radio.pack(anchor="w", padx=10, pady=5)

        # User logo selection
        user_logo_frame = ctk.CTkFrame(selection_frame)
        user_logo_frame.pack(fill="x", padx=30, pady=5)

        self.user_logo_entry = ctk.CTkEntry(
            user_logo_frame,
            textvariable=self.user_logo_path_var,
            width=300,
            state="disabled" if not self.use_user_logo_var.get() else "normal"
        )
        self.user_logo_entry.pack(side="left", padx=5)

        self.browse_logo_button = ctk.CTkButton(
            user_logo_frame,
            text="Przeglądaj...",
            command=self.browse_user_logo,
            width=100,
            state="disabled" if not self.use_user_logo_var.get() else "normal"
        )
        self.browse_logo_button.pack(side="left", padx=5)

    def setup_report_tab(self):
        """Setup report configuration tab"""
        frame = ctk.CTkScrollableFrame(self.report_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Report settings section
        report_section = ctk.CTkFrame(frame)
        report_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(report_section, text="Ustawienia raportów:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

        # Include thumbnails
        ctk.CTkCheckBox(
            report_section,
            text="Dołączaj miniatury w raportach",
            variable=self.report_include_thumbnails_var
        ).pack(anchor="w", padx=20, pady=5)

        # Include details
        ctk.CTkCheckBox(
            report_section,
            text="Dołączaj szczegółowe informacje",
            variable=self.report_include_details_var
        ).pack(anchor="w", padx=20, pady=5)

        # Language selection
        lang_frame = ctk.CTkFrame(report_section)
        lang_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(lang_frame, text="Język raportów:").pack(side="left", padx=5)

        ctk.CTkRadioButton(
            lang_frame,
            text="Polski",
            variable=self.report_language_var,
            value="pl"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            lang_frame,
            text="English",
            variable=self.report_language_var,
            value="en"
        ).pack(side="left", padx=10)

    def setup_display_tab(self):
        """Setup display settings tab"""
        frame = ctk.CTkScrollableFrame(self.display_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # List display section
        list_section = ctk.CTkFrame(frame)
        list_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(list_section, text="Wyświetlanie list:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

        # Show thumbnails in lists
        ctk.CTkCheckBox(
            list_section,
            text="Pokazuj miniatury w listach",
            variable=self.list_show_thumbnails_var
        ).pack(anchor="w", padx=20, pady=5)

        # Theme section
        theme_section = ctk.CTkFrame(frame)
        theme_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(theme_section, text="Motyw aplikacji:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

        # Theme mode
        mode_frame = ctk.CTkFrame(theme_section)
        mode_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(mode_frame, text="Tryb:").pack(side="left", padx=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="Ciemny",
            variable=self.theme_mode_var,
            value="dark"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            mode_frame,
            text="Jasny",
            variable=self.theme_mode_var,
            value="light"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            mode_frame,
            text="Systemowy",
            variable=self.theme_mode_var,
            value="system"
        ).pack(side="left", padx=10)

        # Color theme
        color_frame = ctk.CTkFrame(theme_section)
        color_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(color_frame, text="Kolor:").pack(side="left", padx=5)

        ctk.CTkRadioButton(
            color_frame,
            text="Niebieski",
            variable=self.color_theme_var,
            value="blue"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            color_frame,
            text="Zielony",
            variable=self.color_theme_var,
            value="green"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            color_frame,
            text="Ciemny niebieski",
            variable=self.color_theme_var,
            value="dark-blue"
        ).pack(side="left", padx=10)

    def setup_export_tab(self):
        """Setup export settings tab"""
        frame = ctk.CTkScrollableFrame(self.export_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Export format section
        format_section = ctk.CTkFrame(frame)
        format_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(format_section, text="Format eksportu:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

        format_frame = ctk.CTkFrame(format_section)
        format_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkRadioButton(
            format_frame,
            text="Excel (XLSX)",
            variable=self.export_format_var,
            value="xlsx"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            format_frame,
            text="PDF",
            variable=self.export_format_var,
            value="pdf"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            format_frame,
            text="Word (DOCX)",
            variable=self.export_format_var,
            value="docx"
        ).pack(side="left", padx=10)

        # Export options
        options_section = ctk.CTkFrame(frame)
        options_section.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(options_section, text="Opcje eksportu:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)

        ctk.CTkCheckBox(
            options_section,
            text="Dołączaj załączniki",
            variable=self.export_include_attachments_var
        ).pack(anchor="w", padx=20, pady=5)

        ctk.CTkCheckBox(
            options_section,
            text="Kompresuj obrazy",
            variable=self.export_compress_images_var
        ).pack(anchor="w", padx=20, pady=5)

        # Image quality slider
        quality_frame = ctk.CTkFrame(options_section)
        quality_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(quality_frame, text="Jakość obrazów:").pack(side="left", padx=5)

        self.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=10,
            to=100,
            variable=self.export_image_quality_var,
            width=200
        )
        self.quality_slider.pack(side="left", padx=10)

        self.quality_label = ctk.CTkLabel(quality_frame, text=f"{self.export_image_quality_var.get()}%")
        self.quality_label.pack(side="left", padx=5)

        # Update quality label when slider changes
        self.quality_slider.configure(command=self.update_quality_label)

    def update_quality_label(self, value):
        """Update quality label when slider changes"""
        self.quality_label.configure(text=f"{int(value)}%")

    def on_logo_selection_changed(self):
        """Handle logo selection radio button change"""
        use_user = self.use_user_logo_var.get()
        state = "normal" if use_user else "disabled"
        self.user_logo_entry.configure(state=state)
        self.browse_logo_button.configure(state=state)

    def browse_user_logo(self):
        """Browse for user logo file"""
        filename = filedialog.askopenfilename(
            title="Wybierz logo użytkownika",
            filetypes=[
                ("Pliki obrazów", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        if filename:
            self.user_logo_path_var.set(filename)
            # Preview the selected logo
            self.preview_selected_logo(filename)

    def preview_selected_logo(self, path):
        """Preview selected logo"""
        try:
            img = Image.open(path)
            img.thumbnail((200, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.logo_preview_label.configure(image=photo, text="")
            self.logo_preview_label.image = photo  # Keep reference
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować obrazu: {e}")

    def update_logo_preview(self):
        """Update logo preview with current logo"""
        logo_path = self.settings_manager.get_active_logo_path()
        if logo_path:
            try:
                img = Image.open(logo_path)
                img.thumbnail((200, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.logo_preview_label.configure(image=photo, text="")
                self.logo_preview_label.image = photo  # Keep reference
            except:
                self.logo_preview_label.configure(image="", text="Brak logo")
        else:
            self.logo_preview_label.configure(image="", text="Brak logo")

    def load_current_settings(self):
        """Load current settings into form fields"""
        # Settings are already loaded via variables
        pass

    def save_settings(self):
        """Save settings and close dialog"""
        try:
            # Update settings from form fields
            self.settings.company_name = self.company_name_var.get()
            self.settings.company_address = self.address_textbox.get("1.0", "end-1c") if hasattr(self, 'address_textbox') else ""
            self.settings.company_phone = self.company_phone_var.get()
            self.settings.company_email = self.company_email_var.get()
            self.settings.company_nip = self.company_nip_var.get()
            self.settings.company_regon = self.company_regon_var.get()

            # Logo settings
            if self.use_user_logo_var.get():
                new_logo_path = self.user_logo_path_var.get()
                if new_logo_path and new_logo_path != self.settings.user_logo_path:
                    if not self.settings_manager.set_user_logo(new_logo_path):
                        messagebox.showerror("Błąd", "Nie udało się ustawić logo użytkownika")
                        return
            else:
                self.settings.use_user_logo = False

            # Report settings
            self.settings.report_include_thumbnails = self.report_include_thumbnails_var.get()
            self.settings.report_include_details = self.report_include_details_var.get()
            self.settings.report_language = self.report_language_var.get()

            # Display settings
            self.settings.list_show_thumbnails = self.list_show_thumbnails_var.get()
            self.settings.theme_mode = self.theme_mode_var.get()
            self.settings.color_theme = self.color_theme_var.get()

            # Export settings
            self.settings.export_format = self.export_format_var.get()
            self.settings.export_include_attachments = self.export_include_attachments_var.get()
            self.settings.export_compress_images = self.export_compress_images_var.get()
            self.settings.export_image_quality = self.export_image_quality_var.get()

            # Save to file
            if self.settings_manager.save_settings():
                messagebox.showinfo("Sukces", "Ustawienia zostały zapisane")

                # Apply theme changes
                ctk.set_appearance_mode(self.settings.theme_mode)
                ctk.set_default_color_theme(self.settings.color_theme)

                # Call callback if provided
                if self.callback:
                    self.callback()

                self.destroy()
            else:
                messagebox.showerror("Błąd", "Nie udało się zapisać ustawień")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas zapisywania ustawień: {e}")

    def reset_to_defaults(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz przywrócić ustawienia domyślne?"):
            self.settings_manager.settings = ApplicationSettings()
            self.settings_manager.save_settings()

            # Reload form
            self.setup_variables()
            self.load_current_settings()
            self.update_logo_preview()

            messagebox.showinfo("Sukces", "Przywrócono ustawienia domyślne")

    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')