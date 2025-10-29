#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quotations Module - Phase 2
System Zarządzania Ofertami dla Laser/Prasa
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List, Dict
from decimal import Decimal
import json

# Import głównych komponentów z mfg_app
from mfg_app import SupabaseManager, STATUS_COLORS, STATUS_NAMES
from attachments_gui_widgets import AttachmentsWidget
from attachments_manager import AttachmentsManager

@dataclass
class Quotation:
    """Model oferty"""
    id: Optional[str] = None
    quote_no: str = ""
    customer_id: str = ""
    title: str = ""
    status: str = "DRAFT"
    total_price: float = 0.0
    cost_estimate: float = 0.0
    margin_percent: float = 30.0
    valid_until: Optional[str] = None
    created_at: Optional[str] = None
    converted_to_order: Optional[str] = None
    notes: str = ""
    items: List[Dict] = None

QUOTE_STATUSES = {
    'DRAFT': 'Szkic',
    'SENT': 'Wysłana',
    'NEGOTIATION': 'Negocjacje',
    'ACCEPTED': 'Zaakceptowana',
    'REJECTED': 'Odrzucona',
    'EXPIRED': 'Wygasła',
    'CONVERTED': 'Zamówienie'
}

QUOTE_STATUS_COLORS = {
    'DRAFT': '#808080',
    'SENT': '#4169E1',
    'NEGOTIATION': '#FFA500',
    'ACCEPTED': '#32CD32',
    'REJECTED': '#DC143C',
    'EXPIRED': '#696969',
    'CONVERTED': '#228B22'
}

class QuotationManager(SupabaseManager):
    """Rozszerzona klasa do obsługi ofert"""
    
    def setup_quotation_tables(self):
        """Setup tables for quotations - execute in Supabase SQL"""
        sql_script = """
        -- Tabela ofert
        CREATE TABLE IF NOT EXISTS quotations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            quote_no TEXT UNIQUE NOT NULL,
            customer_id UUID REFERENCES customers(id),
            title TEXT NOT NULL,
            status TEXT DEFAULT 'DRAFT',
            total_price NUMERIC(12,2) DEFAULT 0,
            cost_estimate NUMERIC(12,2) DEFAULT 0,
            margin_percent NUMERIC(5,2) DEFAULT 30,
            valid_until DATE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            converted_to_order UUID REFERENCES orders(id),
            notes TEXT
        );
        
        -- Pozycje oferty
        CREATE TABLE IF NOT EXISTS quotation_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            quotation_id UUID REFERENCES quotations(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price NUMERIC(10,2),
            total_price NUMERIC(12,2),
            material TEXT,
            processing_type TEXT,
            notes TEXT
        );
        
        -- Licznik numerów ofert
        CREATE TABLE IF NOT EXISTS quote_counters (
            year INTEGER PRIMARY KEY,
            last_no INTEGER DEFAULT 0
        );
        
        -- Funkcja generowania numeru oferty
        CREATE OR REPLACE FUNCTION next_quote_no_fn()
        RETURNS TEXT AS $$
        DECLARE
            v_year INTEGER;
            v_next_no INTEGER;
        BEGIN
            v_year := EXTRACT(YEAR FROM NOW());
            
            INSERT INTO quote_counters(year, last_no) 
            VALUES (v_year, 0)
            ON CONFLICT (year) DO NOTHING;
            
            UPDATE quote_counters 
            SET last_no = last_no + 1
            WHERE year = v_year
            RETURNING last_no INTO v_next_no;
            
            RETURN 'Q' || v_year::TEXT || '-' || LPAD(v_next_no::TEXT, 5, '0');
        END;
        $$ LANGUAGE plpgsql;
        
        -- Trigger dla automatycznego numeru oferty
        CREATE OR REPLACE FUNCTION set_quote_no_before_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.quote_no IS NULL OR LENGTH(NEW.quote_no) = 0 THEN
                NEW.quote_no := next_quote_no_fn();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trg_set_quote_no ON quotations;
        CREATE TRIGGER trg_set_quote_no
        BEFORE INSERT ON quotations
        FOR EACH ROW
        EXECUTE FUNCTION set_quote_no_before_insert();
        
        -- RLS dla ofert
        ALTER TABLE quotations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE quotation_items ENABLE ROW LEVEL SECURITY;
        ALTER TABLE quote_counters ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY quotations_anon_all ON quotations
            FOR ALL TO anon USING (true) WITH CHECK (true);
        CREATE POLICY quotation_items_anon_all ON quotation_items
            FOR ALL TO anon USING (true) WITH CHECK (true);
        CREATE POLICY quote_counters_anon_all ON quote_counters
            FOR ALL TO anon USING (true) WITH CHECK (true);
        """
        return sql_script
    
    def get_quotations(self, filters=None):
        """Pobierz oferty"""
        try:
            query = self.client.table('quotations').select("*, customers(name)")
            
            if filters:
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                if filters.get('customer_id'):
                    query = query.eq('customer_id', filters['customer_id'])
                if filters.get('date_from'):
                    query = query.gte('created_at', filters['date_from'])
                if filters.get('date_to'):
                    query = query.lte('created_at', filters['date_to'])
            
            response = query.order('created_at', desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error getting quotations: {e}")
            return []
    
    def create_quotation(self, quotation: Quotation):
        """Utwórz ofertę"""
        try:
            data = {
                'customer_id': quotation.customer_id,
                'title': quotation.title,
                'status': quotation.status,
                'total_price': quotation.total_price,
                'cost_estimate': quotation.cost_estimate,
                'margin_percent': quotation.margin_percent,
                'valid_until': quotation.valid_until,
                'notes': quotation.notes
            }
            response = self.client.table('quotations').insert(data).execute()
            
            if response.data and quotation.items:
                quote_id = response.data[0]['id']
                for item in quotation.items:
                    item['quotation_id'] = quote_id
                    self.client.table('quotation_items').insert(item).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating quotation: {e}")
            return None
    
    def convert_to_order(self, quotation_id: str):
        """Konwertuj ofertę na zamówienie"""
        try:
            # Pobierz ofertę
            quote_response = self.client.table('quotations').select("*").eq('id', quotation_id).execute()
            if not quote_response.data:
                return None
            
            quote = quote_response.data[0]
            
            # Pobierz pozycje oferty
            items_response = self.client.table('quotation_items').select("*").eq('quotation_id', quotation_id).execute()
            
            # Utwórz zamówienie
            order_data = {
                'customer_id': quote['customer_id'],
                'title': quote['title'],
                'price_pln': quote['total_price'],
                'status': 'RECEIVED',
                'received_at': datetime.now().date().isoformat(),
                'notes': f"Konwersja z oferty {quote['quote_no']}\n{quote.get('notes', '')}"
            }
            
            order_response = self.client.table('orders').insert(order_data).execute()
            
            if order_response.data:
                order_id = order_response.data[0]['id']
                
                # Dodaj części do zamówienia
                for item in items_response.data:
                    part_data = {
                        'order_id': order_id,
                        'name': item['description'],
                        'material': item.get('material', ''),
                        'qty': item.get('quantity', 1)
                    }
                    self.client.table('parts').insert(part_data).execute()

                # Kopiuj załączniki z oferty do zamówienia
                attachments_manager = AttachmentsManager(self.client)
                copied_count = attachments_manager.copy_attachments(
                    source_entity_type='quotation',
                    source_entity_id=quotation_id,
                    target_entity_type='order',
                    target_entity_id=order_id,
                    created_by='system'
                )

                if copied_count > 0:
                    print(f"✅ Skopiowano {copied_count} załączników z oferty do zamówienia")

                # Zaktualizuj ofertę
                self.client.table('quotations').update({
                    'status': 'CONVERTED',
                    'converted_to_order': order_id
                }).eq('id', quotation_id).execute()

                return order_response.data[0]
            
            return None
        except Exception as e:
            print(f"Error converting quotation: {e}")
            return None

class QuotationDialog(ctk.CTkToplevel):
    """Dialog tworzenia/edycji oferty"""
    
    def __init__(self, parent, db: QuotationManager, quotation_data=None):
        super().__init__(parent)
        self.db = db
        self.quotation_data = quotation_data
        self.items = []
        self.quotation_id = quotation_data['id'] if quotation_data else None

        self.title("Edycja oferty" if quotation_data else "Nowa oferta")
        self.geometry("1100x700")
        
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        if quotation_data:
            self.load_quotation_data()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup UI for quotation dialog"""
        # Main scrollable container
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text="💼 Nowa oferta cenowa",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=10)
        
        # Customer and title section
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        # Customer selection
        ctk.CTkLabel(info_frame, text="Klient:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        customers = self.db.get_customers()
        self.customer_map = {c['name']: c['id'] for c in customers}
        self.customer_combo = ctk.CTkComboBox(
            info_frame,
            values=list(self.customer_map.keys()),
            width=300
        )
        self.customer_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Title
        ctk.CTkLabel(info_frame, text="Tytuł oferty:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.title_entry = ctk.CTkEntry(info_frame, width=400)
        self.title_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        # Pricing section
        pricing_frame = ctk.CTkFrame(main_frame)
        pricing_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            pricing_frame,
            text="📊 Kalkulacja cenowa",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        calc_grid = ctk.CTkFrame(pricing_frame)
        calc_grid.pack(padx=20, pady=10)
        
        # Cost estimate
        ctk.CTkLabel(calc_grid, text="Szacowany koszt:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cost_entry = ctk.CTkEntry(calc_grid, width=150)
        self.cost_entry.grid(row=0, column=1, padx=5, pady=5)
        self.cost_entry.bind("<KeyRelease>", self.calculate_price)
        
        # Margin
        ctk.CTkLabel(calc_grid, text="Marża [%]:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.margin_entry = ctk.CTkEntry(calc_grid, width=100)
        self.margin_entry.grid(row=0, column=3, padx=5, pady=5)
        self.margin_entry.insert(0, "30")
        self.margin_entry.bind("<KeyRelease>", self.calculate_price)
        
        # Total price
        ctk.CTkLabel(calc_grid, text="Cena całkowita:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.price_entry = ctk.CTkEntry(calc_grid, width=150)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Calculate button
        ctk.CTkButton(
            calc_grid,
            text="🔄 Przelicz",
            width=100,
            command=self.calculate_price
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Validity
        ctk.CTkLabel(calc_grid, text="Ważna do:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        from tkcalendar import DateEntry
        self.valid_date = DateEntry(calc_grid, width=12)
        self.valid_date.set_date(datetime.now().date() + timedelta(days=30))
        self.valid_date.grid(row=1, column=4, padx=5, pady=5)
        
        # Items section
        items_frame = ctk.CTkFrame(main_frame)
        items_frame.pack(fill="both", expand=True, pady=10)
        
        items_header = ctk.CTkFrame(items_frame)
        items_header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            items_header,
            text="📝 Pozycje oferty",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)
        
        # Items buttons
        items_btn_frame = ctk.CTkFrame(items_header)
        items_btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            items_btn_frame,
            text="➕ Dodaj pozycję",
            width=120,
            command=self.add_item
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            items_btn_frame,
            text="🗑️ Usuń",
            width=100,
            command=self.delete_item
        ).pack(side="left", padx=5)
        
        # Items list
        self.items_tree = ttk.Treeview(
            items_frame,
            columns=('desc', 'material', 'processing', 'qty', 'unit_price', 'total'),
            show='headings',
            height=8
        )
        
        self.items_tree.heading('desc', text='Opis')
        self.items_tree.heading('material', text='Materiał')
        self.items_tree.heading('processing', text='Obróbka')
        self.items_tree.heading('qty', text='Ilość')
        self.items_tree.heading('unit_price', text='Cena jedn.')
        self.items_tree.heading('total', text='Razem')
        
        self.items_tree.column('desc', width=250)
        self.items_tree.column('material', width=150)
        self.items_tree.column('processing', width=150)
        self.items_tree.column('qty', width=80)
        self.items_tree.column('unit_price', width=100)
        self.items_tree.column('total', width=100)
        
        self.items_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Notes
        notes_frame = ctk.CTkFrame(main_frame)
        notes_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(notes_frame, text="Uwagi:").pack(anchor="w", padx=10, pady=5)
        self.notes_text = ctk.CTkTextbox(notes_frame, height=100)
        self.notes_text.pack(fill="x", padx=10, pady=5)

        # Załączniki
        self.attachments_widget = AttachmentsWidget(
            main_frame,
            db_client=self.db.client,
            entity_type='quotation',
            entity_id=self.quotation_id
        )
        self.attachments_widget.pack(fill="both", expand=True, padx=5, pady=10)

        # Bottom buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Zapisz ofertę",
            width=200,
            height=40,
            command=self.save_quotation,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=20)
        
        ctk.CTkButton(
            btn_frame,
            text="📄 Generuj PDF",
            width=150,
            height=40,
            command=self.generate_pdf
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            width=150,
            height=40,
            command=self.destroy
        ).pack(side="right", padx=20)
    
    def calculate_price(self, event=None):
        """Kalkuluj cenę na podstawie kosztu i marży"""
        try:
            cost = float(self.cost_entry.get() or 0)
            margin = float(self.margin_entry.get() or 0)
            
            if cost > 0:
                total = cost * (1 + margin / 100)
                self.price_entry.delete(0, 'end')
                self.price_entry.insert(0, f"{total:.2f}")
        except ValueError:
            pass
    
    def add_item(self):
        """Dodaj pozycję do oferty"""
        dialog = QuotationItemDialog(self)
        self.wait_window(dialog)
        
        if hasattr(dialog, 'item_data'):
            self.items.append(dialog.item_data)
            self.items_tree.insert('', 'end', values=(
                dialog.item_data['description'],
                dialog.item_data.get('material', ''),
                dialog.item_data.get('processing_type', ''),
                dialog.item_data.get('quantity', 1),
                f"{dialog.item_data.get('unit_price', 0):.2f}",
                f"{dialog.item_data.get('total_price', 0):.2f}"
            ))
            self.update_total()
    
    def delete_item(self):
        """Usuń wybraną pozycję"""
        selection = self.items_tree.selection()
        if selection:
            index = self.items_tree.index(selection[0])
            del self.items[index]
            self.items_tree.delete(selection[0])
            self.update_total()
    
    def update_total(self):
        """Aktualizuj całkowitą cenę oferty"""
        total = sum(item.get('total_price', 0) for item in self.items)
        self.price_entry.delete(0, 'end')
        self.price_entry.insert(0, f"{total:.2f}")
    
    def save_quotation(self):
        """Zapisz ofertę"""
        customer = self.customer_combo.get()
        if not customer:
            messagebox.showwarning("Uwaga", "Wybierz klienta")
            return
        
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Uwaga", "Podaj tytuł oferty")
            return
        
        quotation = Quotation(
            customer_id=self.customer_map[customer],
            title=title,
            status='DRAFT',
            total_price=float(self.price_entry.get() or 0),
            cost_estimate=float(self.cost_entry.get() or 0),
            margin_percent=float(self.margin_entry.get() or 30),
            valid_until=self.valid_date.get_date().isoformat(),
            notes=self.notes_text.get("1.0", "end-1c"),
            items=self.items
        )
        
        result = self.db.create_quotation(quotation)
        if result:
            # Ustaw ID dla widgetu załączników
            self.quotation_id = result['id']
            self.attachments_widget.set_entity_id(result['id'])

            messagebox.showinfo("Sukces", f"Oferta {result['quote_no']} została utworzona")
            # Nie zamykaj okna, aby użytkownik mógł dodać załączniki
            # self.destroy()
        else:
            messagebox.showerror("Błąd", "Nie udało się utworzyć oferty")
    
    def generate_pdf(self):
        """Generuj PDF z ofertą"""
        from tkinter import filedialog
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Oferta_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        
        if not file_path:
            return
        
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1F4E79'),
                spaceAfter=30,
                alignment=1
            )
            
            elements.append(Paragraph("OFERTA CENOWA", header_style))
            elements.append(Spacer(1, 20))
            
            # Company info
            company_info = """
            <para align=center>
            <b>Twoja Firma Sp. z o.o.</b><br/>
            ul. Produkcyjna 123<br/>
            00-000 Miasto<br/>
            NIP: 123-456-78-90<br/>
            Tel: +48 123 456 789
            </para>
            """
            elements.append(Paragraph(company_info, styles['Normal']))
            elements.append(Spacer(1, 30))
            
            # Customer info
            customer = self.customer_combo.get()
            elements.append(Paragraph(f"<b>Dla:</b> {customer}", styles['Normal']))
            elements.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Paragraph(f"<b>Ważna do:</b> {self.valid_date.get_date()}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Title
            elements.append(Paragraph(f"<b>Przedmiot oferty:</b> {self.title_entry.get()}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Items table
            if self.items:
                data = [['Lp.', 'Opis', 'Materiał', 'Ilość', 'Cena jedn.', 'Razem']]
                
                for i, item in enumerate(self.items, 1):
                    data.append([
                        str(i),
                        item['description'],
                        item.get('material', ''),
                        item.get('quantity', 1),
                        f"{item.get('unit_price', 0):.2f} PLN",
                        f"{item.get('total_price', 0):.2f} PLN"
                    ])
                
                # Add total row
                total = sum(item.get('total_price', 0) for item in self.items)
                data.append(['', '', '', '', 'RAZEM:', f"{total:.2f} PLN"])
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, -1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
            
            # Notes
            if self.notes_text.get("1.0", "end-1c").strip():
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("<b>Uwagi:</b>", styles['Normal']))
                elements.append(Paragraph(self.notes_text.get("1.0", "end-1c"), styles['Normal']))
            
            # Footer
            elements.append(Spacer(1, 40))
            footer = """
            <para align=center fontSize=10>
            Oferta ważna 30 dni od daty wystawienia.<br/>
            Termin realizacji: do uzgodnienia.<br/>
            Płatność: przelew 14 dni.
            </para>
            """
            elements.append(Paragraph(footer, styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Sukces", f"PDF został wygenerowany:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd generowania PDF:\n{e}")
    
    def load_quotation_data(self):
        """Załaduj dane oferty do edycji"""
        # Implementation for loading existing quotation data
        pass

class QuotationItemDialog(ctk.CTkToplevel):
    """Dialog dodawania pozycji do oferty"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Nowa pozycja oferty")
        self.geometry("600x500")
        
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Center
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup UI for item dialog"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Description
        ctk.CTkLabel(main_frame, text="Opis pozycji*:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        self.desc_text = ctk.CTkTextbox(main_frame, height=100)
        self.desc_text.pack(fill="x", pady=5)
        
        # Material
        ctk.CTkLabel(main_frame, text="Materiał:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        materials = ["Stal S235", "Stal S355", "Stal nierdzewna 304", "Stal nierdzewna 316", 
                    "Aluminium", "Mosiądz", "Miedź", "Inne"]
        self.material_combo = ctk.CTkComboBox(main_frame, values=materials, width=400)
        self.material_combo.pack(pady=5)
        
        # Processing type
        ctk.CTkLabel(main_frame, text="Typ obróbki:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
        processing = ["Cięcie laserowe", "Gięcie na prasie", "Cięcie + Gięcie", 
                     "Spawanie", "Obróbka mechaniczna", "Inne"]
        self.processing_combo = ctk.CTkComboBox(main_frame, values=processing, width=400)
        self.processing_combo.pack(pady=5)
        
        # Quantity and price
        grid_frame = ctk.CTkFrame(main_frame)
        grid_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(grid_frame, text="Ilość:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.qty_entry = ctk.CTkEntry(grid_frame, width=100)
        self.qty_entry.grid(row=0, column=1, padx=5, pady=5)
        self.qty_entry.insert(0, "1")
        self.qty_entry.bind("<KeyRelease>", self.calculate_total)
        
        ctk.CTkLabel(grid_frame, text="Cena jednostkowa [PLN]:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.price_entry = ctk.CTkEntry(grid_frame, width=150)
        self.price_entry.grid(row=0, column=3, padx=5, pady=5)
        self.price_entry.bind("<KeyRelease>", self.calculate_total)
        
        ctk.CTkLabel(grid_frame, text="Razem [PLN]:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.total_label = ctk.CTkLabel(grid_frame, text="0.00", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_label.grid(row=1, column=1, padx=5, pady=5)
        
        # Notes
        ctk.CTkLabel(main_frame, text="Uwagi:").pack(anchor="w", pady=5)
        self.notes_entry = ctk.CTkEntry(main_frame, width=400)
        self.notes_entry.pack(pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Dodaj",
            width=150,
            command=self.save_item
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            width=150,
            command=self.destroy
        ).pack(side="right", padx=10)
    
    def calculate_total(self, event=None):
        """Oblicz wartość całkowitą pozycji"""
        try:
            qty = int(self.qty_entry.get() or 1)
            price = float(self.price_entry.get() or 0)
            total = qty * price
            self.total_label.configure(text=f"{total:.2f}")
        except ValueError:
            self.total_label.configure(text="0.00")
    
    def save_item(self):
        """Zapisz pozycję"""
        desc = self.desc_text.get("1.0", "end-1c").strip()
        if not desc:
            messagebox.showwarning("Uwaga", "Opis pozycji jest wymagany")
            return
        
        try:
            qty = int(self.qty_entry.get() or 1)
            unit_price = float(self.price_entry.get() or 0)
            total_price = qty * unit_price
        except ValueError:
            messagebox.showwarning("Uwaga", "Nieprawidłowe wartości liczbowe")
            return
        
        self.item_data = {
            'description': desc,
            'material': self.material_combo.get(),
            'processing_type': self.processing_combo.get(),
            'quantity': qty,
            'unit_price': unit_price,
            'total_price': total_price,
            'notes': self.notes_entry.get()
        }
        
        self.destroy()

class QuotationsWindow(ctk.CTkToplevel):
    """Główne okno modułu ofert"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("System Ofertowania - Faza 2")
        self.geometry("1300x700")
        
        # Initialize extended database manager
        self.db = QuotationManager()
        
        self.setup_ui()
        self.load_quotations()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1300 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup UI for quotations window"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text="💼 System Ofertowania",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(header)
        btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Nowa oferta",
            width=150,
            height=35,
            command=self.new_quotation
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Konwertuj na zamówienie",
            width=180,
            height=35,
            command=self.convert_to_order
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="📊 Statystyki",
            width=120,
            height=35,
            command=self.show_statistics
        ).pack(side="left", padx=5)
        
        # Main content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Filters
        filter_frame = ctk.CTkFrame(content_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Status:").pack(side="left", padx=10)
        self.status_filter = ctk.CTkComboBox(
            filter_frame,
            values=["Wszystkie"] + list(QUOTE_STATUSES.values()),
            width=150
        )
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.set("Wszystkie")
        
        ctk.CTkButton(
            filter_frame,
            text="Filtruj",
            width=100,
            command=self.apply_filters
        ).pack(side="left", padx=10)
        
        # Quotations list
        tree_frame = ctk.CTkFrame(content_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.quotes_tree = ttk.Treeview(
            tree_frame,
            columns=('quote_no', 'customer', 'title', 'status', 'total', 'valid_until', 'created'),
            show='headings'
        )
        
        self.quotes_tree.heading('quote_no', text='Nr oferty')
        self.quotes_tree.heading('customer', text='Klient')
        self.quotes_tree.heading('title', text='Tytuł')
        self.quotes_tree.heading('status', text='Status')
        self.quotes_tree.heading('total', text='Wartość')
        self.quotes_tree.heading('valid_until', text='Ważna do')
        self.quotes_tree.heading('created', text='Utworzona')
        
        # Configure columns
        self.quotes_tree.column('quote_no', width=120)
        self.quotes_tree.column('customer', width=200)
        self.quotes_tree.column('title', width=250)
        self.quotes_tree.column('status', width=120)
        self.quotes_tree.column('total', width=120)
        self.quotes_tree.column('valid_until', width=100)
        self.quotes_tree.column('created', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.quotes_tree.yview)
        self.quotes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.quotes_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure tags for status colors
        for status, color in QUOTE_STATUS_COLORS.items():
            self.quotes_tree.tag_configure(status, background=color, foreground='white')
    
    def load_quotations(self, filters=None):
        """Załaduj oferty"""
        self.quotes_tree.delete(*self.quotes_tree.get_children())
        
        quotations = self.db.get_quotations(filters)
        
        for quote in quotations:
            customer_name = quote['customers']['name'] if quote.get('customers') else ''
            
            self.quotes_tree.insert('', 'end',
                values=(
                    quote.get('quote_no', ''),
                    customer_name,
                    quote.get('title', ''),
                    QUOTE_STATUSES.get(quote.get('status', 'DRAFT')),
                    f"{quote.get('total_price', 0):.2f} PLN",
                    quote.get('valid_until', ''),
                    quote.get('created_at', '')[:10]
                ),
                tags=(quote.get('status', 'DRAFT'), quote['id'])
            )
    
    def new_quotation(self):
        """Utwórz nową ofertę"""
        dialog = QuotationDialog(self, self.db)
        self.wait_window(dialog)
        self.load_quotations()
    
    def convert_to_order(self):
        """Konwertuj ofertę na zamówienie"""
        selection = self.quotes_tree.selection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz ofertę do konwersji")
            return
        
        item = self.quotes_tree.item(selection[0])
        quote_id = item['tags'][1]
        quote_no = item['values'][0]
        
        if messagebox.askyesno("Potwierdzenie", 
                               f"Czy konwertować ofertę {quote_no} na zamówienie?"):
            result = self.db.convert_to_order(quote_id)
            if result:
                messagebox.showinfo("Sukces", 
                    f"Oferta została przekształcona w zamówienie {result.get('process_no', '')}")
                self.load_quotations()
            else:
                messagebox.showerror("Błąd", "Nie udało się konwertować oferty")
    
    def apply_filters(self):
        """Zastosuj filtry"""
        filters = {}
        
        status = self.status_filter.get()
        if status != "Wszystkie":
            for key, value in QUOTE_STATUSES.items():
                if value == status:
                    filters['status'] = key
                    break
        
        self.load_quotations(filters)
    
    def show_statistics(self):
        """Pokaż statystyki ofert"""
        # Implementation for quotation statistics
        pass

# Eksport klas do użycia w głównej aplikacji
__all__ = ['QuotationManager', 'QuotationsWindow', 'QuotationDialog']
