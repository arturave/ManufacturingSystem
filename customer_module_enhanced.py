#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Customer Management Module
Full CRUD functionality with extended customer data
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import re
from datetime import datetime
import json

@dataclass
class CustomerExtended:
    """Extended Customer model with all business fields"""
    id: Optional[str] = None
    name: str = ""                          # Pełna nazwa firmy
    short_name: str = ""                    # Nazwa skrócona
    nip: str = ""                          # NIP
    regon: str = ""                        # REGON
    krs: str = ""                          # KRS (opcjonalny)
    email: str = ""                        # Email główny firmy
    website: str = ""                      # Strona WWW
    phone: str = ""                        # Telefon główny
    address: str = ""                      # Adres
    city: str = ""                         # Miasto
    postal_code: str = ""                  # Kod pocztowy
    country: str = "Polska"                # Kraj
    contact_person: str = ""               # Osoba kontaktowa
    contact_phone: str = ""                # Telefon osoby kontaktowej
    contact_email: str = ""                # Email osoby kontaktowej
    contact_position: str = ""             # Stanowisko osoby kontaktowej
    notes: str = ""                        # Uwagi
    customer_type: str = "company"         # Typ: company/individual
    is_active: bool = True                 # Czy aktywny
    credit_limit: float = 0.0              # Limit kredytowy
    payment_terms: int = 14                # Termin płatności (dni)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CustomerValidator:
    """Validator for customer data"""
    
    @staticmethod
    def validate_nip(nip: str) -> bool:
        """Validate Polish NIP number"""
        nip = nip.replace('-', '').replace(' ', '')
        if not nip or len(nip) != 10:
            return False
        
        try:
            weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
            check_sum = sum(int(nip[i]) * weights[i] for i in range(9))
            return (check_sum % 11) % 10 == int(nip[9])
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def validate_regon(regon: str) -> bool:
        """Validate Polish REGON number"""
        regon = regon.replace('-', '').replace(' ', '')
        if not regon or len(regon) not in [9, 14]:
            return False
        
        try:
            if len(regon) == 9:
                weights = [8, 9, 2, 3, 4, 5, 6, 7]
                check_sum = sum(int(regon[i]) * weights[i] for i in range(8))
                return check_sum % 11 == int(regon[8])
            else:  # 14 digits
                weights = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
                check_sum = sum(int(regon[i]) * weights[i] for i in range(13))
                return check_sum % 11 == int(regon[13])
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) if email else True
    
    @staticmethod
    def validate_website(url: str) -> bool:
        """Validate website URL"""
        if not url:
            return True
        pattern = r'^(https?://)?([\w\-]+\.)+[\w\-]{2,}(/.*)?$'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number"""
        if not phone:
            return True
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Check if it's a valid phone (7-15 digits)
        return bool(re.match(r'^\d{7,15}$', cleaned))
    
    @staticmethod
    def format_nip(nip: str) -> str:
        """Format NIP with dashes"""
        nip = nip.replace('-', '').replace(' ', '')
        if len(nip) == 10:
            return f"{nip[:3]}-{nip[3:6]}-{nip[6:8]}-{nip[8:]}"
        return nip
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number"""
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if len(cleaned) == 9 and not cleaned.startswith('+'):
            # Polish mobile
            return f"{cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned.startswith('48'):
            # Polish with country code
            return f"+48 {cleaned[2:5]} {cleaned[5:8]} {cleaned[8:]}"
        return phone

class CustomerSearchDialog(ctk.CTkToplevel):
    """Advanced customer search dialog"""
    
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.selected_customer = None
        
        self.title("Wyszukiwanie zaawansowane")
        self.geometry("800x600")
        
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 400
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup search UI"""
        # Search criteria frame
        criteria_frame = ctk.CTkFrame(self)
        criteria_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            criteria_frame,
            text="Kryteria wyszukiwania",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Search fields
        ctk.CTkLabel(criteria_frame, text="Nazwa:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.name_search = ctk.CTkEntry(criteria_frame, width=200)
        self.name_search.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(criteria_frame, text="NIP:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.nip_search = ctk.CTkEntry(criteria_frame, width=150)
        self.nip_search.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(criteria_frame, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.email_search = ctk.CTkEntry(criteria_frame, width=200)
        self.email_search.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(criteria_frame, text="Miasto:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.city_search = ctk.CTkEntry(criteria_frame, width=150)
        self.city_search.grid(row=2, column=3, padx=5, pady=5)
        
        # Search button
        ctk.CTkButton(
            criteria_frame,
            text="🔍 Szukaj",
            command=self.search_customers
        ).grid(row=3, column=0, columnspan=4, pady=10)
        
        # Results frame
        results_frame = ctk.CTkFrame(self)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Results tree
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=('name', 'nip', 'city', 'email'),
            show='headings',
            selectmode='browse'
        )
        
        self.results_tree.heading('name', text='Nazwa')
        self.results_tree.heading('nip', text='NIP')
        self.results_tree.heading('city', text='Miasto')
        self.results_tree.heading('email', text='Email')
        
        self.results_tree.column('name', width=250)
        self.results_tree.column('nip', width=120)
        self.results_tree.column('city', width=150)
        self.results_tree.column('email', width=200)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Wybierz",
            command=self.select_customer
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            command=self.destroy
        ).pack(side="right", padx=5)
    
    def search_customers(self):
        """Search customers based on criteria"""
        # This would connect to the database
        # For now, using mock data
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Here you would call: customers = self.db.search_customers(criteria)
        # Mock results for demonstration
        results = [
            {'name': 'Firma ABC', 'nip': '123-456-78-90', 'city': 'Warszawa', 'email': 'abc@example.com'},
            {'name': 'XYZ Sp. z o.o.', 'nip': '987-654-32-10', 'city': 'Kraków', 'email': 'xyz@example.com'}
        ]
        
        for customer in results:
            self.results_tree.insert('', 'end', values=(
                customer['name'],
                customer['nip'],
                customer['city'],
                customer['email']
            ))
    
    def select_customer(self):
        """Select customer from results"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            self.selected_customer = item['values']
            self.destroy()

class CustomerEditDialog(ctk.CTkToplevel):
    """Enhanced customer edit dialog with all fields"""
    
    def __init__(self, parent, db, customer_data=None):
        super().__init__(parent)
        self.db = db
        self.customer_data = customer_data
        self.validator = CustomerValidator()
        
        self.title("Edycja klienta" if customer_data else "Nowy klient")
        self.geometry("1000x700")
        
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        if customer_data:
            self.load_customer_data()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 500
        y = (self.winfo_screenheight() // 2) - 350
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup comprehensive customer edit UI"""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="👥 Dane klienta",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Tab view for organized sections
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs
        self.tabview.add("Podstawowe")
        self.tabview.add("Kontakt")
        self.tabview.add("Adres")
        self.tabview.add("Finansowe")
        self.tabview.add("Dodatkowe")
        
        # Setup each tab
        self.setup_basic_tab()
        self.setup_contact_tab()
        self.setup_address_tab()
        self.setup_financial_tab()
        self.setup_additional_tab()
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Zapisz",
            width=150,
            command=self.save_customer,
            fg_color="green"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="✔️ Sprawdź NIP",
            width=150,
            command=self.validate_nip_regon
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🌐 Pobierz z GUS",
            width=150,
            command=self.fetch_from_gus
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Anuluj",
            width=150,
            command=self.destroy
        ).pack(side="right", padx=5)
    
    def setup_basic_tab(self):
        """Setup basic information tab"""
        tab = self.tabview.tab("Podstawowe")
        
        # Company type selection
        type_frame = ctk.CTkFrame(tab)
        type_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(type_frame, text="Typ klienta:").pack(side="left", padx=5)
        
        self.customer_type = ctk.CTkSegmentedButton(
            type_frame,
            values=["Firma", "Osoba fizyczna"],
            command=self.on_type_change
        )
        self.customer_type.pack(side="left", padx=10)
        self.customer_type.set("Firma")
        
        # Basic fields frame
        fields_frame = ctk.CTkFrame(tab)
        fields_frame.pack(fill="x", pady=10)
        
        # Row 1
        row = 0
        ctk.CTkLabel(fields_frame, text="Pełna nazwa:*").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ctk.CTkEntry(fields_frame, width=400)
        self.name_entry.grid(row=row, column=1, columnspan=3, padx=5, pady=5)
        
        # Row 2
        row += 1
        ctk.CTkLabel(fields_frame, text="Nazwa skrócona:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.short_name_entry = ctk.CTkEntry(fields_frame, width=200)
        self.short_name_entry.grid(row=row, column=1, padx=5, pady=5)
        
        # Row 3
        row += 1
        ctk.CTkLabel(fields_frame, text="NIP:*").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.nip_entry = ctk.CTkEntry(fields_frame, width=150)
        self.nip_entry.grid(row=row, column=1, padx=5, pady=5)
        self.nip_entry.bind("<FocusOut>", self.on_nip_change)
        
        self.nip_status = ctk.CTkLabel(fields_frame, text="", text_color="gray")
        self.nip_status.grid(row=row, column=2, padx=5, pady=5)
        
        # Row 4
        row += 1
        ctk.CTkLabel(fields_frame, text="REGON:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.regon_entry = ctk.CTkEntry(fields_frame, width=150)
        self.regon_entry.grid(row=row, column=1, padx=5, pady=5)
        self.regon_entry.bind("<FocusOut>", self.on_regon_change)
        
        self.regon_status = ctk.CTkLabel(fields_frame, text="", text_color="gray")
        self.regon_status.grid(row=row, column=2, padx=5, pady=5)
        
        # Row 5
        row += 1
        ctk.CTkLabel(fields_frame, text="KRS:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.krs_entry = ctk.CTkEntry(fields_frame, width=150)
        self.krs_entry.grid(row=row, column=1, padx=5, pady=5)
        
        # Row 6
        row += 1
        ctk.CTkLabel(fields_frame, text="Status:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.is_active = ctk.CTkSwitch(fields_frame, text="Aktywny", width=100)
        self.is_active.grid(row=row, column=1, padx=5, pady=5)
        self.is_active.select()
    
    def setup_contact_tab(self):
        """Setup contact information tab"""
        tab = self.tabview.tab("Kontakt")
        
        # Company contact frame
        company_frame = ctk.CTkFrame(tab)
        company_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            company_frame,
            text="Dane kontaktowe firmy",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        row = 1
        ctk.CTkLabel(company_frame, text="Email główny:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.email_entry = ctk.CTkEntry(company_frame, width=300)
        self.email_entry.grid(row=row, column=1, padx=5, pady=5)
        self.email_entry.bind("<FocusOut>", self.on_email_change)
        
        self.email_status = ctk.CTkLabel(company_frame, text="", text_color="gray")
        self.email_status.grid(row=row, column=2, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(company_frame, text="Telefon główny:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.phone_entry = ctk.CTkEntry(company_frame, width=200)
        self.phone_entry.grid(row=row, column=1, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(company_frame, text="Strona WWW:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.website_entry = ctk.CTkEntry(company_frame, width=300)
        self.website_entry.grid(row=row, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            company_frame,
            text="🌐",
            width=30,
            command=self.open_website
        ).grid(row=row, column=2, padx=5, pady=5)
        
        # Separator
        separator = ctk.CTkFrame(tab, height=2)
        separator.pack(fill="x", pady=10)
        
        # Contact person frame
        person_frame = ctk.CTkFrame(tab)
        person_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            person_frame,
            text="Osoba kontaktowa",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        row = 1
        ctk.CTkLabel(person_frame, text="Imię i nazwisko:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.contact_person_entry = ctk.CTkEntry(person_frame, width=300)
        self.contact_person_entry.grid(row=row, column=1, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(person_frame, text="Stanowisko:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.contact_position_entry = ctk.CTkEntry(person_frame, width=300)
        self.contact_position_entry.grid(row=row, column=1, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(person_frame, text="Telefon bezpośredni:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.contact_phone_entry = ctk.CTkEntry(person_frame, width=200)
        self.contact_phone_entry.grid(row=row, column=1, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(person_frame, text="Email bezpośredni:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.contact_email_entry = ctk.CTkEntry(person_frame, width=300)
        self.contact_email_entry.grid(row=row, column=1, padx=5, pady=5)
    
    def setup_address_tab(self):
        """Setup address tab"""
        tab = self.tabview.tab("Adres")
        
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", pady=10)
        
        row = 0
        ctk.CTkLabel(frame, text="Ulica i numer:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.address_entry = ctk.CTkEntry(frame, width=400)
        self.address_entry.grid(row=row, column=1, columnspan=2, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(frame, text="Kod pocztowy:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.postal_code_entry = ctk.CTkEntry(frame, width=100)
        self.postal_code_entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        
        row += 1
        ctk.CTkLabel(frame, text="Miasto:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.city_entry = ctk.CTkEntry(frame, width=250)
        self.city_entry.grid(row=row, column=1, padx=5, pady=5)
        
        row += 1
        ctk.CTkLabel(frame, text="Kraj:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        countries = ["Polska", "Niemcy", "Czechy", "Słowacja", "Ukraina", "Litwa", "Inne"]
        self.country_combo = ctk.CTkComboBox(frame, values=countries, width=200)
        self.country_combo.grid(row=row, column=1, padx=5, pady=5)
        self.country_combo.set("Polska")
        
        # Map button
        ctk.CTkButton(
            frame,
            text="🗺️ Pokaż na mapie",
            command=self.show_on_map
        ).grid(row=row+1, column=0, columnspan=2, pady=20)
    
    def setup_financial_tab(self):
        """Setup financial information tab"""
        tab = self.tabview.tab("Finansowe")
        
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", pady=10)
        
        row = 0
        ctk.CTkLabel(frame, text="Limit kredytowy [PLN]:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.credit_limit_entry = ctk.CTkEntry(frame, width=150)
        self.credit_limit_entry.grid(row=row, column=1, padx=5, pady=5)
        self.credit_limit_entry.insert(0, "0.00")
        
        row += 1
        ctk.CTkLabel(frame, text="Termin płatności [dni]:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        payment_terms = ["0", "7", "14", "21", "30", "45", "60", "90"]
        self.payment_terms_combo = ctk.CTkComboBox(frame, values=payment_terms, width=100)
        self.payment_terms_combo.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        self.payment_terms_combo.set("14")
        
        row += 1
        ctk.CTkLabel(frame, text="Rabat [%]:").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        self.discount_slider = ctk.CTkSlider(frame, from_=0, to=50, width=200)
        self.discount_slider.grid(row=row, column=1, padx=5, pady=5)
        self.discount_slider.set(0)
        
        self.discount_label = ctk.CTkLabel(frame, text="0%")
        self.discount_label.grid(row=row, column=2, padx=5, pady=5)
        self.discount_slider.configure(command=self.update_discount_label)
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(
            stats_frame,
            text="Statystyki klienta",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Liczba zamówień: 0\nŁączna wartość: 0.00 PLN\nŚrednia wartość: 0.00 PLN\nOstatnie zamówienie: -",
            justify="left"
        )
        self.stats_label.pack(pady=10)
        
        if self.customer_data:
            self.load_customer_statistics()
    
    def setup_additional_tab(self):
        """Setup additional information tab"""
        tab = self.tabview.tab("Dodatkowe")
        
        # Notes section
        notes_frame = ctk.CTkFrame(tab)
        notes_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(
            notes_frame,
            text="Uwagi i notatki",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)
        
        self.notes_text = ctk.CTkTextbox(notes_frame, height=200)
        self.notes_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tags section
        tags_frame = ctk.CTkFrame(tab)
        tags_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(tags_frame, text="Tagi:").pack(side="left", padx=10)
        
        self.tags_entry = ctk.CTkEntry(tags_frame, width=300, placeholder_text="np. VIP, Partner, Dystrybutor")
        self.tags_entry.pack(side="left", padx=5)
        
        # Audit info
        if self.customer_data:
            audit_frame = ctk.CTkFrame(tab)
            audit_frame.pack(fill="x", pady=20)
            
            created = self.customer_data.get('created_at', 'N/A')
            updated = self.customer_data.get('updated_at', created)
            
            audit_text = f"Utworzono: {created[:19] if created != 'N/A' else 'N/A'}\nZmodyfikowano: {updated[:19] if updated != 'N/A' else 'N/A'}"
            
            ctk.CTkLabel(
                audit_frame,
                text=audit_text,
                text_color="gray",
                font=ctk.CTkFont(size=11)
            ).pack(pady=5)
    
    def on_type_change(self, value):
        """Handle customer type change"""
        is_company = value == "Firma"
        # Enable/disable relevant fields
        self.nip_entry.configure(state="normal" if is_company else "disabled")
        self.regon_entry.configure(state="normal" if is_company else "disabled")
        self.krs_entry.configure(state="normal" if is_company else "disabled")
    
    def on_nip_change(self, event):
        """Validate NIP on field change"""
        nip = self.nip_entry.get()
        if nip:
            if self.validator.validate_nip(nip):
                self.nip_status.configure(text="✅ Poprawny", text_color="green")
                formatted = self.validator.format_nip(nip)
                self.nip_entry.delete(0, 'end')
                self.nip_entry.insert(0, formatted)
            else:
                self.nip_status.configure(text="❌ Niepoprawny", text_color="red")
        else:
            self.nip_status.configure(text="", text_color="gray")
    
    def on_regon_change(self, event):
        """Validate REGON on field change"""
        regon = self.regon_entry.get()
        if regon:
            if self.validator.validate_regon(regon):
                self.regon_status.configure(text="✅ Poprawny", text_color="green")
            else:
                self.regon_status.configure(text="❌ Niepoprawny", text_color="red")
        else:
            self.regon_status.configure(text="", text_color="gray")
    
    def on_email_change(self, event):
        """Validate email on field change"""
        email = self.email_entry.get()
        if email:
            if self.validator.validate_email(email):
                self.email_status.configure(text="✅", text_color="green")
            else:
                self.email_status.configure(text="❌ Niepoprawny format", text_color="red")
        else:
            self.email_status.configure(text="", text_color="gray")
    
    def validate_nip_regon(self):
        """Validate NIP and REGON"""
        nip = self.nip_entry.get()
        regon = self.regon_entry.get()
        
        errors = []
        
        if nip and not self.validator.validate_nip(nip):
            errors.append("NIP jest niepoprawny")
        
        if regon and not self.validator.validate_regon(regon):
            errors.append("REGON jest niepoprawny")
        
        if errors:
            messagebox.showwarning("Błędy walidacji", "\n".join(errors))
        else:
            messagebox.showinfo("Walidacja", "NIP i REGON są poprawne")
    
    def fetch_from_gus(self):
        """Fetch company data from GUS API (mock)"""
        nip = self.nip_entry.get().replace('-', '')
        
        if not nip:
            messagebox.showwarning("Uwaga", "Wprowadź NIP aby pobrać dane z GUS")
            return
        
        # This would connect to real GUS API
        # For demonstration, using mock data
        messagebox.showinfo("Info", 
            "Funkcja pobierania z GUS wymaga integracji z API GUS.\n"
            "W wersji produkcyjnej dane zostaną pobrane automatycznie.")
        
        # Mock data fill
        if nip == "1234567890":
            self.name_entry.delete(0, 'end')
            self.name_entry.insert(0, "Przykładowa Firma Sp. z o.o.")
            self.short_name_entry.delete(0, 'end')
            self.short_name_entry.insert(0, "Przykładowa")
            self.regon_entry.delete(0, 'end')
            self.regon_entry.insert(0, "123456789")
            self.address_entry.delete(0, 'end')
            self.address_entry.insert(0, "ul. Przemysłowa 10")
            self.city_entry.delete(0, 'end')
            self.city_entry.insert(0, "Warszawa")
            self.postal_code_entry.delete(0, 'end')
            self.postal_code_entry.insert(0, "00-001")
    
    def open_website(self):
        """Open customer website"""
        import webbrowser
        url = self.website_entry.get()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
    
    def show_on_map(self):
        """Show address on map"""
        import webbrowser
        address = f"{self.address_entry.get()}, {self.postal_code_entry.get()} {self.city_entry.get()}, {self.country_combo.get()}"
        if address.strip():
            url = f"https://www.google.com/maps/search/{address.replace(' ', '+')}"
            webbrowser.open(url)
    
    def update_discount_label(self, value):
        """Update discount label"""
        self.discount_label.configure(text=f"{int(value)}%")
    
    def load_customer_statistics(self):
        """Load customer statistics from database"""
        # This would load real statistics from database
        # Mock data for demonstration
        stats_text = (
            "Liczba zamówień: 15\n"
            "Łączna wartość: 45,320.00 PLN\n"
            "Średnia wartość: 3,021.33 PLN\n"
            "Ostatnie zamówienie: 2025-01-10"
        )
        self.stats_label.configure(text=stats_text)
    
    def load_customer_data(self):
        """Load existing customer data into form"""
        if not self.customer_data:
            return

        # Basic tab - use 'or' to convert None to empty string
        self.name_entry.insert(0, self.customer_data.get('name') or '')
        self.short_name_entry.insert(0, self.customer_data.get('short_name') or '')
        self.nip_entry.insert(0, self.customer_data.get('nip') or '')
        self.regon_entry.insert(0, self.customer_data.get('regon') or '')
        self.krs_entry.insert(0, self.customer_data.get('krs') or '')

        if not self.customer_data.get('is_active', True):
            self.is_active.deselect()

        # Contact tab - use 'or' to convert None to empty string
        self.email_entry.insert(0, self.customer_data.get('email') or '')
        self.phone_entry.insert(0, self.customer_data.get('phone') or '')
        self.website_entry.insert(0, self.customer_data.get('website') or '')
        self.contact_person_entry.insert(0, self.customer_data.get('contact_person') or '')
        self.contact_position_entry.insert(0, self.customer_data.get('contact_position') or '')
        self.contact_phone_entry.insert(0, self.customer_data.get('contact_phone') or '')
        self.contact_email_entry.insert(0, self.customer_data.get('contact_email') or '')

        # Address tab - use 'or' to convert None to empty string
        self.address_entry.insert(0, self.customer_data.get('address') or '')
        self.postal_code_entry.insert(0, self.customer_data.get('postal_code') or '')
        self.city_entry.insert(0, self.customer_data.get('city') or '')
        self.country_combo.set(self.customer_data.get('country') or 'Polska')

        # Financial tab
        self.credit_limit_entry.delete(0, 'end')
        self.credit_limit_entry.insert(0, str(self.customer_data.get('credit_limit') or 0))
        self.payment_terms_combo.set(str(self.customer_data.get('payment_terms') or 14))

        # Additional tab - use 'or' to convert None to empty string
        self.notes_text.insert("1.0", self.customer_data.get('notes') or '')
    
    def save_customer(self):
        """Save customer data"""
        # Validate required fields
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Uwaga", "Nazwa firmy jest wymagana")
            return
        
        # Validate NIP for companies
        if self.customer_type.get() == "Firma":
            nip = self.nip_entry.get().strip()
            if not nip:
                messagebox.showwarning("Uwaga", "NIP jest wymagany dla firm")
                return
            if not self.validator.validate_nip(nip):
                messagebox.showwarning("Uwaga", "NIP jest niepoprawny")
                return
        
        # Validate emails
        email = self.email_entry.get().strip()
        if email and not self.validator.validate_email(email):
            messagebox.showwarning("Uwaga", "Email główny ma niepoprawny format")
            return
        
        contact_email = self.contact_email_entry.get().strip()
        if contact_email and not self.validator.validate_email(contact_email):
            messagebox.showwarning("Uwaga", "Email kontaktowy ma niepoprawny format")
            return
        
        # Prepare customer data
        customer_data = {
            'name': name,
            'short_name': self.short_name_entry.get().strip(),
            'nip': self.nip_entry.get().strip(),
            'regon': self.regon_entry.get().strip(),
            'krs': self.krs_entry.get().strip(),
            'email': email,
            'website': self.website_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'address': self.address_entry.get().strip(),
            'city': self.city_entry.get().strip(),
            'postal_code': self.postal_code_entry.get().strip(),
            'country': self.country_combo.get(),
            'contact_person': self.contact_person_entry.get().strip(),
            'contact_phone': self.contact_phone_entry.get().strip(),
            'contact_email': contact_email,
            'contact_position': self.contact_position_entry.get().strip(),
            'notes': self.notes_text.get("1.0", "end-1c").strip(),
            'customer_type': 'company' if self.customer_type.get() == "Firma" else 'individual',
            'is_active': self.is_active.get() == 1,
            'credit_limit': float(self.credit_limit_entry.get() or 0),
            'payment_terms': int(self.payment_terms_combo.get() or 14)
        }
        
        try:
            if self.customer_data and 'id' in self.customer_data:
                # Update existing customer
                customer_data['updated_at'] = datetime.now().isoformat()
                if self.db.update_customer(self.customer_data['id'], customer_data):
                    messagebox.showinfo("Sukces", "Dane klienta zostały zaktualizowane")
                    self.destroy()
                else:
                    messagebox.showerror("Błąd", "Nie udało się zaktualizować danych klienta")
            else:
                # Create new customer
                customer = CustomerExtended(**customer_data)
                if self.db.create_customer(customer):
                    messagebox.showinfo("Sukces", "Klient został dodany")
                    self.destroy()
                else:
                    messagebox.showerror("Błąd", "Nie udało się dodać klienta")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd: {str(e)}")

class CustomerExportDialog(ctk.CTkToplevel):
    """Dialog for exporting customer data"""
    
    def __init__(self, parent, customers):
        super().__init__(parent)
        self.customers = customers
        
        self.title("Eksport danych klientów")
        self.geometry("500x400")
        
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 200
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup export UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="📤 Eksport danych klientów",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)
        
        # Format selection
        format_frame = ctk.CTkFrame(self)
        format_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            format_frame,
            text="Wybierz format eksportu:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=5)
        
        self.format_var = ctk.StringVar(value="excel")
        
        formats = [
            ("Excel (.xlsx)", "excel"),
            ("CSV (.csv)", "csv"),
            ("JSON (.json)", "json"),
            ("PDF (.pdf)", "pdf"),
            ("vCard (.vcf)", "vcard")
        ]
        
        for text, value in formats:
            ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value
            ).pack(anchor="w", padx=20, pady=2)
        
        # Options
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Opcje eksportu:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=5)
        
        self.include_inactive = ctk.CTkCheckBox(options_frame, text="Uwzględnij nieaktywnych")
        self.include_inactive.pack(anchor="w", padx=20, pady=2)
        
        self.include_notes = ctk.CTkCheckBox(options_frame, text="Uwzględnij uwagi")
        self.include_notes.pack(anchor="w", padx=20, pady=2)
        self.include_notes.select()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="📥 Eksportuj",
            command=self.export_data,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            command=self.destroy,
            width=150
        ).pack(side="right", padx=5)
    
    def export_data(self):
        """Export customer data to selected format"""
        format_type = self.format_var.get()
        
        from tkinter import filedialog
        
        # Get file path
        if format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if file_path:
                self.export_to_excel(file_path)
        
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            if file_path:
                self.export_to_csv(file_path)
        
        elif format_type == "json":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )
            if file_path:
                self.export_to_json(file_path)
        
        elif format_type == "pdf":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            if file_path:
                self.export_to_pdf(file_path)
        
        elif format_type == "vcard":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".vcf",
                filetypes=[("vCard files", "*.vcf")]
            )
            if file_path:
                self.export_to_vcard(file_path)
    
    def export_to_excel(self, file_path):
        """Export to Excel format"""
        import pandas as pd
        
        try:
            # Filter customers
            customers = self.customers
            if not self.include_inactive.get():
                customers = [c for c in customers if c.get('is_active', True)]
            
            # Prepare data
            df = pd.DataFrame(customers)
            
            # Select columns to export
            columns = ['name', 'short_name', 'nip', 'regon', 'krs', 
                      'email', 'phone', 'website', 'address', 'city', 
                      'postal_code', 'contact_person', 'contact_phone', 'contact_email']
            
            if self.include_notes.get():
                columns.append('notes')
            
            df = df[columns]
            
            # Save to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Klienci', index=False)
                
                # Auto-adjust columns width
                worksheet = writer.sheets['Klienci']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{file_path}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {str(e)}")
    
    def export_to_csv(self, file_path):
        """Export to CSV format"""
        import csv
        
        try:
            customers = self.customers
            if not self.include_inactive.get():
                customers = [c for c in customers if c.get('is_active', True)]
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                if customers:
                    fieldnames = ['name', 'short_name', 'nip', 'regon', 'email', 
                                 'phone', 'city', 'contact_person']
                    if self.include_notes.get():
                        fieldnames.append('notes')
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(customers)
            
            messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{file_path}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {str(e)}")
    
    def export_to_json(self, file_path):
        """Export to JSON format"""
        try:
            customers = self.customers
            if not self.include_inactive.get():
                customers = [c for c in customers if c.get('is_active', True)]
            
            if not self.include_notes.get():
                for customer in customers:
                    customer.pop('notes', None)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{file_path}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {str(e)}")
    
    def export_to_pdf(self, file_path):
        """Export to PDF format"""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph("Lista Klientów", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # Table data
            data = [['Nazwa', 'NIP', 'Miasto', 'Email', 'Telefon']]
            
            customers = self.customers
            if not self.include_inactive.get():
                customers = [c for c in customers if c.get('is_active', True)]
            
            for customer in customers:
                data.append([
                    customer.get('name', ''),
                    customer.get('nip', ''),
                    customer.get('city', ''),
                    customer.get('email', ''),
                    customer.get('phone', '')
                ])
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{file_path}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {str(e)}")
    
    def export_to_vcard(self, file_path):
        """Export to vCard format"""
        try:
            customers = self.customers
            if not self.include_inactive.get():
                customers = [c for c in customers if c.get('is_active', True)]
            
            vcards = []
            for customer in customers:
                vcard = [
                    "BEGIN:VCARD",
                    "VERSION:3.0",
                    f"FN:{customer.get('name', '')}",
                    f"ORG:{customer.get('name', '')}",
                ]
                
                if customer.get('email'):
                    vcard.append(f"EMAIL:{customer['email']}")
                
                if customer.get('phone'):
                    vcard.append(f"TEL:{customer['phone']}")
                
                if customer.get('website'):
                    vcard.append(f"URL:{customer['website']}")
                
                if customer.get('address'):
                    addr = f"{customer.get('address', '')};{customer.get('city', '')};{customer.get('postal_code', '')}"
                    vcard.append(f"ADR:;;{addr}")
                
                if customer.get('notes') and self.include_notes.get():
                    vcard.append(f"NOTE:{customer['notes']}")
                
                vcard.append("END:VCARD")
                vcards.append('\n'.join(vcard))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(vcards))
            
            messagebox.showinfo("Sukces", f"Dane zostały wyeksportowane do:\n{file_path}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {str(e)}")

# Export for use in main application
__all__ = [
    'CustomerExtended',
    'CustomerValidator', 
    'CustomerEditDialog',
    'CustomerSearchDialog',
    'CustomerExportDialog'
]
