#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook Agent - Phase 3
Automatyzacja obsługi zapytań i zamówień email
"""

import os
import sys
import json
import re
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib
import tempfile

# Windows-specific Outlook integration
try:
    import win32com.client
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    print("⚠️ Biblioteka pywin32 nie jest zainstalowana. Agent Outlook niedostępny.")

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk

# Import database manager
from mfg_app import SupabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outlook_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OutlookAgent')

@dataclass
class EmailTemplate:
    """Szablon email"""
    name: str
    subject: str
    body: str
    attachments: List[str] = None
    
class EmailPattern:
    """Wzorce do rozpoznawania typów emaili"""
    
    INQUIRY_PATTERNS = [
        r'zapytanie',
        r'oferta',
        r'wycena',
        r'proszę o (cenę|wycenę)',
        r'ile kosztuje',
        r'cennik',
        r'quote',
        r'inquiry',
        r'RFQ'
    ]
    
    ORDER_PATTERNS = [
        r'zamówienie',
        r'zlecenie',
        r'order',
        r'PO\s*\d+',
        r'purchase order',
        r'proszę o realizację',
        r'do realizacji'
    ]
    
    URGENT_PATTERNS = [
        r'pilne',
        r'urgent',
        r'ASAP',
        r'natychmiast',
        r'priorytet',
        r'krytyczne',
        r'na wczoraj'
    ]
    
    @staticmethod
    def detect_email_type(subject: str, body: str) -> str:
        """Wykryj typ emaila na podstawie treści"""
        text = f"{subject} {body}".lower()
        
        # Check for urgent markers
        is_urgent = any(re.search(pattern, text) for pattern in EmailPattern.URGENT_PATTERNS)
        
        # Check for order
        if any(re.search(pattern, text) for pattern in EmailPattern.ORDER_PATTERNS):
            return "ORDER_URGENT" if is_urgent else "ORDER"
        
        # Check for inquiry
        if any(re.search(pattern, text) for pattern in EmailPattern.INQUIRY_PATTERNS):
            return "INQUIRY_URGENT" if is_urgent else "INQUIRY"
        
        return "OTHER"

class AttachmentProcessor:
    """Procesor załączników"""
    
    SUPPORTED_FORMATS = {
        'drawings': ['.dxf', '.dwg', '.stp', '.step', '.iges'],
        'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx'],
        'images': ['.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'],
        'archives': ['.zip', '.rar', '.7z']
    }
    
    @staticmethod
    def extract_dimensions(file_path: str) -> Optional[Dict]:
        """Próbuj wyekstrahować wymiary z pliku CAD"""
        # Simplified - in production would use CAD libraries
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.dxf']:
            # Parse DXF for bounding box
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Look for EXTMIN and EXTMAX
                    # This is simplified - real implementation would use ezdxf library
                    return {
                        'format': 'DXF',
                        'units': 'mm',
                        'detected': True
                    }
            except:
                pass
        
        return None
    
    @staticmethod
    def extract_material_info(text: str) -> Dict:
        """Wyekstrahuj informacje o materiale z tekstu"""
        materials = {
            'stal': 'Stal S235',
            's235': 'Stal S235',
            's355': 'Stal S355',
            'nierdzewna': 'Stal nierdzewna 304',
            '304': 'Stal nierdzewna 304',
            '316': 'Stal nierdzewna 316',
            'aluminium': 'Aluminium',
            'alu': 'Aluminium',
            'mosiądz': 'Mosiądz',
            'miedź': 'Miedź'
        }
        
        thickness_pattern = r'(\d+(?:\.\d+)?)\s*(?:mm|milimetr)'
        quantity_pattern = r'(\d+)\s*(?:szt|sztuk|pcs|pieces)'
        
        result = {
            'material': None,
            'thickness': None,
            'quantity': None
        }
        
        text_lower = text.lower()
        
        # Find material
        for key, value in materials.items():
            if key in text_lower:
                result['material'] = value
                break
        
        # Find thickness
        thickness_match = re.search(thickness_pattern, text_lower)
        if thickness_match:
            result['thickness'] = float(thickness_match.group(1))
        
        # Find quantity
        quantity_match = re.search(quantity_pattern, text_lower)
        if quantity_match:
            result['quantity'] = int(quantity_match.group(1))
        
        return result

class OutlookAgent:
    """Agent automatyzujący Outlook"""
    
    def __init__(self, db_manager: SupabaseManager):
        self.db = db_manager
        self.outlook = None
        self.running = False
        self.check_interval = 60  # seconds
        self.processed_emails = set()  # Track processed emails
        self.templates = self.load_templates()
        
        if OUTLOOK_AVAILABLE:
            try:
                self.outlook = win32com.client.Dispatch("Outlook.Application")
                self.namespace = self.outlook.GetNamespace("MAPI")
                logger.info("✅ Połączono z Outlook")
            except Exception as e:
                logger.error(f"❌ Nie można połączyć z Outlook: {e}")
                self.outlook = None
    
    def load_templates(self) -> Dict[str, EmailTemplate]:
        """Załaduj szablony emaili"""
        templates = {
            'inquiry_received': EmailTemplate(
                name='Potwierdzenie zapytania',
                subject='RE: {original_subject} - Potwierdzenie otrzymania zapytania',
                body="""Szanowni Państwo,

Dziękujemy za przesłane zapytanie ofertowe.

Potwierdzamy otrzymanie Państwa zapytania i informujemy, że zostało ono zarejestrowane 
w naszym systemie pod numerem: {inquiry_number}

Nasz zespół przygotuje ofertę w ciągu 24-48 godzin roboczych.
W przypadku pytań prosimy o kontakt.

Z poważaniem,
Zespół Produkcji"""
            ),
            
            'order_confirmation': EmailTemplate(
                name='Potwierdzenie zamówienia',
                subject='Potwierdzenie zamówienia nr {order_number}',
                body="""Szanowni Państwo,

Potwierdzamy przyjęcie zamówienia nr {order_number}.

Szczegóły zamówienia:
- Tytuł: {title}
- Planowana data realizacji: {planned_date}
- Status: {status}

Państwa zamówienie zostało przekazane do realizacji.
O postępach będziemy informować na bieżąco.

Z poważaniem,
Zespół Produkcji"""
            ),
            
            'status_update': EmailTemplate(
                name='Aktualizacja statusu',
                subject='Zamówienie {order_number} - zmiana statusu',
                body="""Szanowni Państwo,

Informujemy o zmianie statusu Państwa zamówienia:

Numer zamówienia: {order_number}
Nowy status: {new_status}
Data aktualizacji: {update_date}

{additional_info}

Z poważaniem,
Zespół Produkcji"""
            ),
            
            'sla_warning': EmailTemplate(
                name='Ostrzeżenie SLA',
                subject='⚠️ Zbliżający się termin realizacji - {order_number}',
                body="""UWAGA - Zbliżający się termin realizacji

Zamówienie: {order_number}
Klient: {customer}
Planowany termin: {planned_date}
Dni do terminu: {days_remaining}

Status: {status}

Prosimy o podjęcie odpowiednich działań.

System Automatyczny"""
            )
        }
        
        return templates
    
    def process_inbox(self):
        """Przetwórz skrzynkę odbiorczą"""
        if not self.outlook:
            logger.error("Outlook nie jest dostępny")
            return
        
        try:
            inbox = self.namespace.GetDefaultFolder(6)  # 6 = Inbox
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)
            
            unread_messages = [msg for msg in messages if msg.UnRead]
            
            logger.info(f"📧 Znaleziono {len(unread_messages)} nieprzeczytanych wiadomości")
            
            for message in unread_messages[:10]:  # Process max 10 at a time
                try:
                    self.process_email(message)
                except Exception as e:
                    logger.error(f"Błąd przetwarzania emaila: {e}")
                    
        except Exception as e:
            logger.error(f"Błąd dostępu do skrzynki: {e}")
    
    def process_email(self, message):
        """Przetwórz pojedynczy email"""
        try:
            # Get email details
            subject = message.Subject
            body = message.Body
            sender = message.SenderEmailAddress
            received_time = message.ReceivedTime
            
            # Create unique ID for tracking
            email_id = hashlib.md5(f"{sender}{received_time}{subject}".encode()).hexdigest()
            
            if email_id in self.processed_emails:
                logger.info(f"Email już przetworzony: {subject}")
                return
            
            logger.info(f"📨 Przetwarzanie: {subject} od {sender}")
            
            # Detect email type
            email_type = EmailPattern.detect_email_type(subject, body)
            logger.info(f"Typ emaila: {email_type}")
            
            # Extract attachments
            attachments = self.extract_attachments(message)
            
            # Extract information
            material_info = AttachmentProcessor.extract_material_info(body)
            
            # Process based on type
            if email_type in ['INQUIRY', 'INQUIRY_URGENT']:
                self.process_inquiry(message, attachments, material_info, urgent=(email_type == 'INQUIRY_URGENT'))
            elif email_type in ['ORDER', 'ORDER_URGENT']:
                self.process_order(message, attachments, material_info, urgent=(email_type == 'ORDER_URGENT'))
            else:
                logger.info(f"Email typu OTHER - pomijam automatyczne przetwarzanie")
            
            # Mark as processed
            self.processed_emails.add(email_id)
            
            # Mark as read
            message.UnRead = False
            message.Save()
            
        except Exception as e:
            logger.error(f"Błąd przetwarzania emaila: {e}")
    
    def extract_attachments(self, message) -> List[Dict]:
        """Wyekstrahuj i zapisz załączniki"""
        attachments = []
        temp_dir = Path(tempfile.gettempdir()) / "outlook_agent"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            for attachment in message.Attachments:
                filename = attachment.FileName
                file_path = temp_dir / filename
                
                # Save attachment
                attachment.SaveAsFile(str(file_path))
                
                # Analyze file
                file_info = {
                    'name': filename,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'extension': file_path.suffix.lower()
                }
                
                # Try to extract CAD dimensions
                if file_info['extension'] in AttachmentProcessor.SUPPORTED_FORMATS['drawings']:
                    dimensions = AttachmentProcessor.extract_dimensions(str(file_path))
                    if dimensions:
                        file_info['dimensions'] = dimensions
                
                attachments.append(file_info)
                logger.info(f"📎 Załącznik: {filename}")
                
        except Exception as e:
            logger.error(f"Błąd ekstraktowania załączników: {e}")
        
        return attachments
    
    def process_inquiry(self, message, attachments, material_info, urgent=False):
        """Przetwórz zapytanie ofertowe"""
        try:
            # Extract customer info
            customer_email = message.SenderEmailAddress
            customer_name = message.SenderName
            
            # Check if customer exists
            customers = self.db.get_customers()
            customer = None
            for c in customers:
                if c.get('contact') and customer_email in c['contact']:
                    customer = c
                    break
            
            # Create customer if not exists
            if not customer:
                from mfg_app import Customer
                new_customer = Customer(
                    name=customer_name or customer_email.split('@')[0],
                    contact=customer_email
                )
                customer = self.db.create_customer(new_customer)
                logger.info(f"✅ Utworzono nowego klienta: {customer_name}")
            
            # Create quotation request
            title = f"Zapytanie: {message.Subject}"
            if urgent:
                title = "🔴 PILNE - " + title
            
            # Send confirmation
            self.send_confirmation_email(
                to=customer_email,
                template='inquiry_received',
                data={
                    'original_subject': message.Subject,
                    'inquiry_number': f"INQ-{datetime.now().strftime('%Y%m%d-%H%M')}"
                }
            )
            
            logger.info(f"✅ Przetworzono zapytanie od {customer_name}")
            
            # Create task notification
            self.create_task_notification(
                f"Nowe zapytanie od {customer_name}",
                f"Temat: {message.Subject}\nPilne: {urgent}\nZałączników: {len(attachments)}",
                priority='high' if urgent else 'normal'
            )
            
        except Exception as e:
            logger.error(f"Błąd przetwarzania zapytania: {e}")
    
    def process_order(self, message, attachments, material_info, urgent=False):
        """Przetwórz zamówienie"""
        try:
            from mfg_app import Order
            
            # Extract customer info
            customer_email = message.SenderEmailAddress
            
            # Find customer
            customers = self.db.get_customers()
            customer = None
            for c in customers:
                if c.get('contact') and customer_email in c['contact']:
                    customer = c
                    break
            
            if not customer:
                logger.warning(f"Nieznany klient: {customer_email}")
                # Create notification for manual processing
                self.create_task_notification(
                    f"Zamówienie od nieznanego klienta",
                    f"Email: {customer_email}\nTemat: {message.Subject}",
                    priority='high'
                )
                return
            
            # Create order
            title = message.Subject.replace('RE:', '').replace('Fwd:', '').strip()
            if urgent:
                title = "🔴 PILNE - " + title
            
            order = Order(
                customer_id=customer['id'],
                title=title,
                status='RECEIVED',
                received_at=datetime.now().date().isoformat(),
                notes=f"Automatyczne import z email\n\n{message.Body[:500]}"
            )
            
            result = self.db.create_order(order)
            
            if result:
                order_no = result.get('process_no', 'N/A')
                logger.info(f"✅ Utworzono zamówienie: {order_no}")
                
                # Upload attachments
                for att in attachments:
                    self.db.upload_file(result['id'], order_no, att['path'])
                
                # Send confirmation
                self.send_confirmation_email(
                    to=customer_email,
                    template='order_confirmation',
                    data={
                        'order_number': order_no,
                        'title': title,
                        'planned_date': 'Do ustalenia',
                        'status': 'Wpłynęło'
                    }
                )
                
                # Create task
                self.create_task_notification(
                    f"Nowe zamówienie {order_no}",
                    f"Klient: {customer['name']}\nPilne: {urgent}",
                    priority='high' if urgent else 'normal'
                )
            
        except Exception as e:
            logger.error(f"Błąd przetwarzania zamówienia: {e}")
    
    def send_confirmation_email(self, to: str, template: str, data: Dict):
        """Wyślij email z potwierdzeniem"""
        if not self.outlook:
            return
        
        try:
            tmpl = self.templates.get(template)
            if not tmpl:
                logger.error(f"Nieznany szablon: {template}")
                return
            
            mail = self.outlook.CreateItem(0)  # 0 = Mail item
            mail.To = to
            mail.Subject = tmpl.subject.format(**data)
            mail.Body = tmpl.body.format(**data)
            
            # Add signature
            mail.Body += "\n\n--\nWiadomość wygenerowana automatycznie\nSystem Zarządzania Produkcją"
            
            mail.Send()
            logger.info(f"✉️ Wysłano potwierdzenie do {to}")
            
        except Exception as e:
            logger.error(f"Błąd wysyłania emaila: {e}")
    
    def create_task_notification(self, title: str, body: str, priority: str = 'normal'):
        """Utwórz zadanie/powiadomienie w Outlook"""
        if not self.outlook:
            return
        
        try:
            task = self.outlook.CreateItem(3)  # 3 = Task item
            task.Subject = title
            task.Body = body
            task.DueDate = datetime.now() + timedelta(days=1)
            
            if priority == 'high':
                task.Importance = 2  # High
            else:
                task.Importance = 1  # Normal
            
            task.Save()
            logger.info(f"📋 Utworzono zadanie: {title}")
            
        except Exception as e:
            logger.error(f"Błąd tworzenia zadania: {e}")
    
    def send_sla_warnings(self):
        """Wyślij ostrzeżenia SLA"""
        try:
            # Get orders with approaching deadlines
            orders = self.db.get_orders()
            today = datetime.now().date()
            
            for order in orders:
                if order.get('planned_at') and not order.get('finished_at'):
                    planned = datetime.fromisoformat(order['planned_at']).date()
                    days_remaining = (planned - today).days
                    
                    # Send warning if deadline in 2 days or less
                    if 0 < days_remaining <= 2:
                        customer = order.get('customer_name', 'N/A')
                        
                        # Find customer email
                        customers = self.db.get_customers()
                        customer_email = None
                        for c in customers:
                            if c['name'] == customer:
                                customer_email = c.get('contact')
                                break
                        
                        if customer_email and '@' in customer_email:
                            self.send_confirmation_email(
                                to=customer_email,
                                template='sla_warning',
                                data={
                                    'order_number': order.get('process_no', 'N/A'),
                                    'customer': customer,
                                    'planned_date': planned.isoformat(),
                                    'days_remaining': days_remaining,
                                    'status': order.get('status', 'N/A')
                                }
                            )
                            
                            logger.info(f"⚠️ Wysłano ostrzeżenie SLA dla {order.get('process_no')}")
            
        except Exception as e:
            logger.error(f"Błąd wysyłania ostrzeżeń SLA: {e}")
    
    def start(self):
        """Uruchom agenta"""
        if not self.outlook:
            logger.error("Outlook nie jest dostępny")
            return False
        
        self.running = True
        
        def run():
            logger.info("🚀 Agent Outlook uruchomiony")
            while self.running:
                try:
                    self.process_inbox()
                    self.send_sla_warnings()
                except Exception as e:
                    logger.error(f"Błąd w pętli agenta: {e}")
                
                time.sleep(self.check_interval)
            
            logger.info("🛑 Agent Outlook zatrzymany")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return True
    
    def stop(self):
        """Zatrzymaj agenta"""
        self.running = False
        logger.info("Zatrzymywanie agenta...")

class OutlookAgentWindow(ctk.CTkToplevel):
    """Okno kontrolne agenta Outlook"""
    
    def __init__(self, parent, db_manager: SupabaseManager):
        super().__init__(parent)
        
        self.title("Agent Outlook - Automatyzacja Email")
        self.geometry("900x600")
        
        self.db = db_manager
        self.agent = OutlookAgent(db_manager)
        
        self.setup_ui()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Start monitoring log
        self.update_log()
    
    def setup_ui(self):
        """Setup UI for agent window"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text="🤖 Agent Outlook - Faza 3",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=20)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            header,
            text="⭕ Zatrzymany",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="right", padx=20)
        
        # Control panel
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ Uruchom agenta",
            width=150,
            command=self.start_agent
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ Zatrzymaj",
            width=150,
            command=self.stop_agent,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
        
        ctk.CTkButton(
            control_frame,
            text="🔄 Sprawdź teraz",
            width=150,
            command=self.check_now
        ).pack(side="left", padx=10)
        
        # Check interval
        ctk.CTkLabel(control_frame, text="Interwał [s]:").pack(side="left", padx=(20, 5))
        self.interval_entry = ctk.CTkEntry(control_frame, width=80)
        self.interval_entry.pack(side="left", padx=5)
        self.interval_entry.insert(0, "60")
        
        ctk.CTkButton(
            control_frame,
            text="Ustaw",
            width=60,
            command=self.set_interval
        ).pack(side="left", padx=5)
        
        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tabview.add("📝 Log aktywności")
        self.tabview.add("⚙️ Konfiguracja")
        self.tabview.add("📧 Szablony")
        self.tabview.add("📊 Statystyki")
        
        # Log tab
        log_tab = self.tabview.tab("📝 Log aktywności")
        
        self.log_text = ctk.CTkTextbox(log_tab, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configuration tab
        config_tab = self.tabview.tab("⚙️ Konfiguracja")
        
        config_frame = ctk.CTkScrollableFrame(config_tab)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Email patterns configuration
        ctk.CTkLabel(
            config_frame,
            text="Wzorce rozpoznawania emaili",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=10)
        
        ctk.CTkLabel(config_frame, text="Wzorce zapytań:").pack(anchor="w", pady=5)
        self.inquiry_patterns = ctk.CTkTextbox(config_frame, height=100)
        self.inquiry_patterns.pack(fill="x", pady=5)
        self.inquiry_patterns.insert("1.0", "\n".join(EmailPattern.INQUIRY_PATTERNS))
        
        ctk.CTkLabel(config_frame, text="Wzorce zamówień:").pack(anchor="w", pady=5)
        self.order_patterns = ctk.CTkTextbox(config_frame, height=100)
        self.order_patterns.pack(fill="x", pady=5)
        self.order_patterns.insert("1.0", "\n".join(EmailPattern.ORDER_PATTERNS))
        
        ctk.CTkLabel(config_frame, text="Wzorce pilności:").pack(anchor="w", pady=5)
        self.urgent_patterns = ctk.CTkTextbox(config_frame, height=100)
        self.urgent_patterns.pack(fill="x", pady=5)
        self.urgent_patterns.insert("1.0", "\n".join(EmailPattern.URGENT_PATTERNS))
        
        ctk.CTkButton(
            config_frame,
            text="💾 Zapisz konfigurację",
            command=self.save_config
        ).pack(pady=20)
        
        # Templates tab
        templates_tab = self.tabview.tab("📧 Szablony")
        
        templates_frame = ctk.CTkScrollableFrame(templates_tab)
        templates_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            templates_frame,
            text="Szablony automatycznych odpowiedzi",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=10)
        
        # Template selector
        template_names = list(self.agent.templates.keys())
        self.template_selector = ctk.CTkComboBox(
            templates_frame,
            values=template_names,
            width=300,
            command=self.load_template
        )
        self.template_selector.pack(pady=10)
        
        # Template editor
        ctk.CTkLabel(templates_frame, text="Temat:").pack(anchor="w", pady=5)
        self.template_subject = ctk.CTkEntry(templates_frame, width=600)
        self.template_subject.pack(pady=5)
        
        ctk.CTkLabel(templates_frame, text="Treść:").pack(anchor="w", pady=5)
        self.template_body = ctk.CTkTextbox(templates_frame, height=300)
        self.template_body.pack(fill="both", expand=True, pady=5)
        
        ctk.CTkButton(
            templates_frame,
            text="💾 Zapisz szablon",
            command=self.save_template
        ).pack(pady=20)
        
        # Statistics tab
        stats_tab = self.tabview.tab("📊 Statystyki")
        
        stats_frame = ctk.CTkFrame(stats_tab)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Statystyki agenta",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.stats_label.pack(pady=20)
        
        self.stats_text = ctk.CTkLabel(
            stats_frame,
            text=self.get_statistics(),
            font=ctk.CTkFont(size=14)
        )
        self.stats_text.pack(pady=10)
        
        # Load first template
        if template_names:
            self.template_selector.set(template_names[0])
            self.load_template(template_names[0])
    
    def start_agent(self):
        """Uruchom agenta"""
        if not OUTLOOK_AVAILABLE:
            messagebox.showerror("Błąd", 
                "Biblioteka pywin32 nie jest zainstalowana.\n"
                "Zainstaluj używając: pip install pywin32")
            return
        
        if self.agent.start():
            self.status_label.configure(text="🟢 Aktywny")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            messagebox.showinfo("Sukces", "Agent Outlook został uruchomiony")
        else:
            messagebox.showerror("Błąd", "Nie udało się uruchomić agenta")
    
    def stop_agent(self):
        """Zatrzymaj agenta"""
        self.agent.stop()
        self.status_label.configure(text="⭕ Zatrzymany")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        messagebox.showinfo("Info", "Agent Outlook został zatrzymany")
    
    def check_now(self):
        """Sprawdź emaile teraz"""
        if not OUTLOOK_AVAILABLE:
            messagebox.showerror("Błąd", "Outlook nie jest dostępny")
            return
        
        try:
            self.agent.process_inbox()
            messagebox.showinfo("Sukces", "Sprawdzono skrzynkę odbiorczą")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd sprawdzania emaili:\n{e}")
    
    def set_interval(self):
        """Ustaw interwał sprawdzania"""
        try:
            interval = int(self.interval_entry.get())
            if interval < 10:
                messagebox.showwarning("Uwaga", "Minimalny interwał to 10 sekund")
                return
            
            self.agent.check_interval = interval
            messagebox.showinfo("Sukces", f"Interwał ustawiony na {interval} sekund")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowa wartość interwału")
    
    def save_config(self):
        """Zapisz konfigurację wzorców"""
        # Update patterns
        EmailPattern.INQUIRY_PATTERNS = self.inquiry_patterns.get("1.0", "end-1c").strip().split('\n')
        EmailPattern.ORDER_PATTERNS = self.order_patterns.get("1.0", "end-1c").strip().split('\n')
        EmailPattern.URGENT_PATTERNS = self.urgent_patterns.get("1.0", "end-1c").strip().split('\n')
        
        # Save to file
        config = {
            'inquiry_patterns': EmailPattern.INQUIRY_PATTERNS,
            'order_patterns': EmailPattern.ORDER_PATTERNS,
            'urgent_patterns': EmailPattern.URGENT_PATTERNS
        }
        
        try:
            with open('outlook_agent_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Sukces", "Konfiguracja została zapisana")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd zapisywania konfiguracji:\n{e}")
    
    def load_template(self, template_name: str):
        """Załaduj szablon do edytora"""
        template = self.agent.templates.get(template_name)
        if template:
            self.template_subject.delete(0, 'end')
            self.template_subject.insert(0, template.subject)
            
            self.template_body.delete("1.0", "end")
            self.template_body.insert("1.0", template.body)
    
    def save_template(self):
        """Zapisz szablon"""
        template_name = self.template_selector.get()
        if template_name in self.agent.templates:
            self.agent.templates[template_name].subject = self.template_subject.get()
            self.agent.templates[template_name].body = self.template_body.get("1.0", "end-1c")
            
            messagebox.showinfo("Sukces", f"Szablon '{template_name}' został zaktualizowany")
    
    def get_statistics(self) -> str:
        """Pobierz statystyki agenta"""
        stats = f"""
📧 Przetworzone emaile: {len(self.agent.processed_emails)}

🔄 Status: {'Aktywny' if self.agent.running else 'Zatrzymany'}

⏰ Interwał sprawdzania: {self.agent.check_interval} sekund

📋 Załadowane szablony: {len(self.agent.templates)}

🔌 Outlook: {'Połączony' if self.agent.outlook else 'Niedostępny'}
        """
        return stats
    
    def update_log(self):
        """Aktualizuj log aktywności"""
        try:
            # Read last lines from log file
            if Path('outlook_agent.log').exists():
                with open('outlook_agent.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-100:]  # Last 100 lines
                    
                    self.log_text.delete("1.0", "end")
                    self.log_text.insert("1.0", "".join(last_lines))
                    self.log_text.see("end")
        except Exception as e:
            print(f"Error updating log: {e}")
        
        # Update statistics
        self.stats_text.configure(text=self.get_statistics())
        
        # Schedule next update
        self.after(2000, self.update_log)  # Update every 2 seconds

# Export for use in main application
__all__ = ['OutlookAgent', 'OutlookAgentWindow', 'EmailPattern', 'AttachmentProcessor']
