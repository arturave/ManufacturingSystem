#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Order Confirmation Dialog
Generates and sends order confirmations as PDF
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
from typing import Dict, List, Optional


class OrderConfirmationDialog(ctk.CTkToplevel):
    """Dialog for generating and sending order confirmations"""

    def __init__(self, parent, db, order_data: Dict, parts_list: List[Dict], mode='print'):
        super().__init__(parent)
        self.db = db
        self.order_data = order_data
        self.parts_list = parts_list
        self.mode = mode  # 'print' or 'email'

        self.title("Potwierdzenie zamówienia")
        self.geometry("800x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Setup UI
        self._setup_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")

        # Load order data if needed
        self._load_order_details()

    def _setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text=f"{'Wydruk' if self.mode == 'print' else 'Wysyłka'} potwierdzenia zamówienia",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack()

        # Options frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)

        # Include prices checkbox
        self.include_prices_var = tk.BooleanVar(value=True)
        self.include_prices_check = ctk.CTkCheckBox(
            options_frame,
            text="Uwzględnij ceny poszczególnych detali",
            variable=self.include_prices_var,
            command=self._update_preview
        )
        self.include_prices_check.pack(side="left", padx=10)

        # Show only total checkbox
        self.show_only_total_var = tk.BooleanVar(value=False)
        self.show_only_total_check = ctk.CTkCheckBox(
            options_frame,
            text="Pokaż tylko sumę całkowitą",
            variable=self.show_only_total_var,
            command=self._toggle_price_options
        )
        self.show_only_total_check.pack(side="left", padx=10)

        # Preview frame
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            preview_frame,
            text="Podgląd potwierdzenia:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)

        # Preview text widget
        self.preview_text = ctk.CTkTextbox(preview_frame, width=750, height=350)
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Email options (if email mode)
        if self.mode == 'email':
            email_frame = ctk.CTkFrame(main_frame)
            email_frame.pack(fill="x", pady=10)

            ctk.CTkLabel(email_frame, text="Email odbiorcy:").pack(side="left", padx=10)
            self.email_entry = ctk.CTkEntry(email_frame, width=300)
            self.email_entry.pack(side="left", padx=5)

            ctk.CTkLabel(email_frame, text="Temat:").pack(side="left", padx=10)
            self.subject_entry = ctk.CTkEntry(email_frame, width=300)
            self.subject_entry.pack(side="left", padx=5)
            self.subject_entry.insert(0, f"Potwierdzenie zamówienia {self.order_data.get('process_no', '')}")

        # Action buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=10)

        if self.mode == 'print':
            ctk.CTkButton(
                button_frame,
                text="💾 Zapisz jako PDF",
                command=self._save_pdf,
                width=150,
                height=35,
                fg_color="blue"
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                button_frame,
                text="🖨️ Drukuj",
                command=self._print_pdf,
                width=150,
                height=35,
                fg_color="green"
            ).pack(side="left", padx=10)
        else:
            ctk.CTkButton(
                button_frame,
                text="✉️ Wyślij email",
                command=self._send_email,
                width=150,
                height=35,
                fg_color="purple"
            ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Anuluj",
            command=self.destroy,
            width=100,
            height=35,
            fg_color="gray"
        ).pack(side="right", padx=10)

        # Initial preview
        self._update_preview()

    def _load_order_details(self):
        """Load complete order details from database"""
        try:
            # Get order ID
            order_id = self.order_data.get('id')
            if not order_id:
                return

            # Load full order data
            response = self.db.client.table('orders').select(
                '*',
                'customers(*)'
            ).eq('id', order_id).execute()

            if response.data:
                self.order_data = response.data[0]

            # Load parts if not provided
            if not self.parts_list:
                parts_response = self.db.client.table('parts').select('*').eq('order_id', order_id).execute()
                if parts_response.data:
                    self.parts_list = parts_response.data

        except Exception as e:
            print(f"Error loading order details: {e}")

    def _toggle_price_options(self):
        """Toggle price display options"""
        if self.show_only_total_var.get():
            self.include_prices_var.set(False)
            self.include_prices_check.configure(state="disabled")
        else:
            self.include_prices_check.configure(state="normal")
        self._update_preview()

    def _update_preview(self):
        """Update the preview text"""
        self.preview_text.delete("1.0", "end")

        # Generate preview text
        preview = self._generate_confirmation_text()
        self.preview_text.insert("1.0", preview)

    def _generate_confirmation_text(self):
        """Generate confirmation text for preview"""
        text = []

        # Header
        text.append("=" * 60)
        text.append("POTWIERDZENIE ZAMÓWIENIA")
        text.append("=" * 60)
        text.append("")

        # Order info
        text.append(f"Nr zamówienia: {self.order_data.get('process_no', 'N/A')}")
        text.append(f"Data: {datetime.now().strftime('%Y-%m-%d')}")
        text.append("")

        # Customer info
        if self.order_data.get('customers'):
            customer = self.order_data['customers']
            text.append("ZAMAWIAJĄCY:")
            text.append(f"  {customer.get('name', '')}")
            if customer.get('address'):
                text.append(f"  {customer.get('address', '')}")
            if customer.get('city') and customer.get('postal_code'):
                text.append(f"  {customer.get('postal_code', '')} {customer.get('city', '')}")
            if customer.get('nip'):
                text.append(f"  NIP: {customer.get('nip', '')}")
            text.append("")

        # Order details
        text.append(f"Tytuł zamówienia: {self.order_data.get('title', '')}")
        text.append(f"Status: {self.order_data.get('status', '')}")
        if self.order_data.get('planned_at'):
            text.append(f"Planowany termin: {self.order_data.get('planned_at', '')[:10]}")
        text.append("")

        # Parts list
        text.append("LISTA DETALI:")
        text.append("-" * 60)

        if self.parts_list:
            if self.include_prices_var.get():
                # With individual prices
                text.append(f"{'Lp.':<5} {'Indeks':<15} {'Nazwa':<25} {'Ilość':<10} {'Cena j.':<12} {'Razem':<12}")
                text.append("-" * 60)

                total = 0
                for i, part in enumerate(self.parts_list, 1):
                    qty = part.get('qty', 1)
                    unit_price = self._calculate_part_price(part)
                    line_total = qty * unit_price
                    total += line_total

                    text.append(
                        f"{i:<5} "
                        f"{part.get('idx_code', '-'):<15} "
                        f"{part.get('name', '')[:25]:<25} "
                        f"{qty:<10} "
                        f"{unit_price:>11.2f} "
                        f"{line_total:>11.2f}"
                    )

                text.append("-" * 60)
                text.append(f"{'SUMA CAŁKOWITA:':<55} {total:>11.2f} PLN")

            elif self.show_only_total_var.get():
                # Only total
                for i, part in enumerate(self.parts_list, 1):
                    text.append(f"{i}. {part.get('name', '')} - Ilość: {part.get('qty', 1)}")

                text.append("-" * 60)
                text.append(f"WARTOŚĆ CAŁKOWITA: {self.order_data.get('price_pln', 0):.2f} PLN")
            else:
                # No prices at all
                for i, part in enumerate(self.parts_list, 1):
                    text.append(f"{i}. {part.get('name', '')} - Ilość: {part.get('qty', 1)}")

        # Notes
        if self.order_data.get('notes'):
            text.append("")
            text.append("UWAGI:")
            text.append(self.order_data.get('notes', ''))

        text.append("")
        text.append("=" * 60)

        return "\n".join(text)

    def _calculate_part_price(self, part):
        """Calculate part unit price"""
        unit_price = part.get('unit_price', 0)
        if unit_price == 0:
            unit_price = (
                part.get('material_laser_cost', 0) +
                part.get('bending_cost', 0) +
                part.get('additional_costs', 0)
            )
        return unit_price

    def _generate_pdf(self, filename):
        """Generate PDF file with order confirmation"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )

            # Container for page elements
            story = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1e40af'),
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )

            normal_style = styles['Normal']
            normal_style.fontSize = 10

            # Title
            story.append(Paragraph("POTWIERDZENIE ZAMÓWIENIA", title_style))
            story.append(Spacer(1, 12))

            # Order info table
            order_info = [
                ['Nr zamówienia:', self.order_data.get('process_no', 'N/A')],
                ['Data:', datetime.now().strftime('%Y-%m-%d')],
                ['Tytuł:', self.order_data.get('title', '')],
                ['Status:', self.order_data.get('status', '')]
            ]

            if self.order_data.get('planned_at'):
                order_info.append(['Planowany termin:', self.order_data.get('planned_at', '')[:10]])

            info_table = Table(order_info, colWidths=[100, 350])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))

            # Customer info
            if self.order_data.get('customers'):
                story.append(Paragraph("ZAMAWIAJĄCY", heading_style))
                customer = self.order_data['customers']
                customer_text = f"<para><b>{customer.get('name', '')}</b><br/>"

                if customer.get('address'):
                    customer_text += f"{customer.get('address', '')}<br/>"
                if customer.get('city') and customer.get('postal_code'):
                    customer_text += f"{customer.get('postal_code', '')} {customer.get('city', '')}<br/>"
                if customer.get('nip'):
                    customer_text += f"NIP: {customer.get('nip', '')}"

                customer_text += "</para>"
                story.append(Paragraph(customer_text, normal_style))
                story.append(Spacer(1, 20))

            # Parts list
            story.append(Paragraph("LISTA DETALI", heading_style))

            if self.parts_list:
                if self.include_prices_var.get():
                    # Table with prices
                    data = [['Lp.', 'Indeks', 'Nazwa', 'Ilość', 'Cena jedn.', 'Razem']]
                    total = 0

                    for i, part in enumerate(self.parts_list, 1):
                        qty = part.get('qty', 1)
                        unit_price = self._calculate_part_price(part)
                        line_total = qty * unit_price
                        total += line_total

                        data.append([
                            str(i),
                            part.get('idx_code', '-'),
                            part.get('name', '')[:40],
                            str(qty),
                            f"{unit_price:.2f} PLN",
                            f"{line_total:.2f} PLN"
                        ])

                    # Add total row
                    data.append(['', '', '', '', 'SUMA:', f"{total:.2f} PLN"])

                    parts_table = Table(data, colWidths=[30, 70, 180, 40, 70, 70])
                    parts_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (3, 0), (5, -1), 'RIGHT'),
                        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
                        ('LINEBELOW', (4, -1), (-1, -1), 2, colors.black),
                        ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (4, -1), (-1, -1), 10),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ]))

                elif self.show_only_total_var.get():
                    # Table without individual prices
                    data = [['Lp.', 'Indeks', 'Nazwa', 'Ilość']]

                    for i, part in enumerate(self.parts_list, 1):
                        data.append([
                            str(i),
                            part.get('idx_code', '-'),
                            part.get('name', '')[:50],
                            str(part.get('qty', 1))
                        ])

                    parts_table = Table(data, colWidths=[30, 80, 250, 50])
                    parts_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ]))
                else:
                    # Simple list without prices
                    data = [['Lp.', 'Nazwa', 'Ilość']]

                    for i, part in enumerate(self.parts_list, 1):
                        data.append([
                            str(i),
                            part.get('name', ''),
                            str(part.get('qty', 1))
                        ])

                    parts_table = Table(data, colWidths=[30, 350, 50])
                    parts_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ]))

                story.append(parts_table)

                # Add total if showing only total
                if self.show_only_total_var.get():
                    story.append(Spacer(1, 20))
                    total_text = f"<para><b>WARTOŚĆ CAŁKOWITA: {self.order_data.get('price_pln', 0):.2f} PLN</b></para>"
                    story.append(Paragraph(total_text, ParagraphStyle(
                        'Total',
                        parent=styles['Normal'],
                        fontSize=12,
                        alignment=TA_RIGHT,
                        textColor=colors.HexColor('#059669')
                    )))

            # Notes
            if self.order_data.get('notes'):
                story.append(Spacer(1, 30))
                story.append(Paragraph("UWAGI", heading_style))
                story.append(Paragraph(self.order_data.get('notes', ''), normal_style))

            # Build PDF
            doc.build(story)

            return True

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować PDF: {e}")
            return False

    def _save_pdf(self):
        """Save confirmation as PDF file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"potwierdzenie_{self.order_data.get('process_no', 'zamowienia')}.pdf"
        )

        if filename:
            if self._generate_pdf(filename):
                messagebox.showinfo("Sukces", f"Potwierdzenie zapisano jako:\n{filename}")

                # Open the file
                if os.name == 'nt':  # Windows
                    os.startfile(filename)
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open {filename}')

    def _print_pdf(self):
        """Print confirmation"""
        # Generate temporary PDF
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            prefix=f"potwierdzenie_{self.order_data.get('process_no', '')}_"
        )
        temp_filename = temp_file.name
        temp_file.close()

        if self._generate_pdf(temp_filename):
            # Open for printing
            if os.name == 'nt':  # Windows
                os.startfile(temp_filename, "print")
            else:
                messagebox.showinfo("Info", f"PDF zapisano jako: {temp_filename}\nOtwórz plik i wydrukuj ręcznie.")

    def _send_email(self):
        """Send confirmation via email"""
        # Get email address
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning("Uwaga", "Podaj adres email odbiorcy")
            return

        # Generate PDF attachment
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            prefix=f"potwierdzenie_{self.order_data.get('process_no', '')}_"
        )
        temp_filename = temp_file.name
        temp_file.close()

        if not self._generate_pdf(temp_filename):
            return

        try:
            # This is a placeholder for email sending
            # In production, you would configure proper SMTP settings
            messagebox.showinfo(
                "Email - Tryb demonstracyjny",
                f"W trybie produkcyjnym email zostałby wysłany na adres:\n{email}\n\n"
                f"Załącznik: {os.path.basename(temp_filename)}\n"
                f"Temat: {self.subject_entry.get()}\n\n"
                "Skonfiguruj ustawienia SMTP, aby włączyć wysyłkę emaili."
            )

            # In production, uncomment and configure:
            # self._send_email_smtp(email, temp_filename)

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wysłać emaila: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def _send_email_smtp(self, recipient_email, pdf_filename):
        """Send email via SMTP (configure settings first)"""
        # SMTP Configuration - adjust these settings
        smtp_server = "smtp.gmail.com"  # or your SMTP server
        smtp_port = 587
        sender_email = "your-email@example.com"
        sender_password = "your-app-password"

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = self.subject_entry.get()

        # Email body
        body = self._generate_confirmation_text()
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        with open(pdf_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_filename)}'
            )
            msg.attach(part)

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        messagebox.showinfo("Sukces", f"Email wysłano na adres: {recipient_email}")