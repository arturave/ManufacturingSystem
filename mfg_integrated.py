#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Manufacturing System Launcher
Combines all phases: Orders, Quotations, and Outlook Agent
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

# Import main application and modules
from mfg_app import MainApplication
from quotations_module import QuotationsWindow
from outlook_agent import OutlookAgentWindow, OUTLOOK_AVAILABLE
from products_module import ProductsWindow

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class IntegratedManufacturingSystem(MainApplication):
    """Extended main application with all phases integrated"""
    
    def __init__(self):
        super().__init__()
        
        # Update title
        self.title("System Zarządzania Produkcją - Wersja Zintegrowana 1.1")
        
        # Add additional menu items
        self.update_menu()
    
    def update_menu(self):
        """Add menu items for Phase 2, 3, and Products"""
        # Find the header frame (first frame in grid)
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                # This should be the header frame
                # Find the button frame
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        # Add new buttons
                        ctk.CTkButton(
                            child,
                            text="💼 Oferty",
                            width=120,
                            height=35,
                            command=self.open_quotations,
                            fg_color="#4CAF50"
                        ).pack(side="left", padx=5)

                        ctk.CTkButton(
                            child,
                            text="📦 Produkty",
                            width=120,
                            height=35,
                            command=self.open_products,
                            fg_color="#9C27B0"
                        ).pack(side="left", padx=5)

                        agent_btn_text = "🤖 Agent" if OUTLOOK_AVAILABLE else "🤖 Agent (N/D)"
                        agent_btn_state = "normal" if OUTLOOK_AVAILABLE else "disabled"

                        ctk.CTkButton(
                            child,
                            text=agent_btn_text,
                            width=120,
                            height=35,
                            command=self.open_outlook_agent,
                            fg_color="#FF6B6B",
                            state=agent_btn_state
                        ).pack(side="left", padx=5)

                        ctk.CTkButton(
                            child,
                            text="ℹ️ O systemie",
                            width=120,
                            height=35,
                            command=self.show_about
                        ).pack(side="left", padx=5)

                        break
                break
    
    def open_quotations(self):
        """Open quotations module (Phase 2)"""
        try:
            quotations_window = QuotationsWindow(self)
            quotations_window.focus()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć modułu ofert:\n{e}")

    def open_products(self):
        """Open products management module"""
        try:
            products_window = ProductsWindow(self, self.db)
            products_window.focus()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć modułu produktów:\n{e}")
    
    def open_outlook_agent(self):
        """Open Outlook Agent (Phase 3)"""
        if not OUTLOOK_AVAILABLE:
            result = messagebox.askyesno(
                "Agent Outlook niedostępny",
                "Biblioteka pywin32 nie jest zainstalowana.\n\n"
                "Aby korzystać z agenta Outlook, zainstaluj:\n"
                "pip install pywin32\n\n"
                "Czy chcesz wyświetlić instrukcję instalacji?"
            )
            if result:
                self.show_installation_guide()
            return
        
        try:
            agent_window = OutlookAgentWindow(self, self.db)
            agent_window.focus()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć agenta Outlook:\n{e}")
    
    def show_installation_guide(self):
        """Show installation guide for pywin32"""
        guide_window = ctk.CTkToplevel(self)
        guide_window.title("Instrukcja instalacji pywin32")
        guide_window.geometry("600x400")
        
        # Center window
        guide_window.update_idletasks()
        x = (guide_window.winfo_screenwidth() // 2) - 300
        y = (guide_window.winfo_screenheight() // 2) - 200
        guide_window.geometry(f"+{x}+{y}")
        
        # Content
        text = ctk.CTkTextbox(guide_window, font=ctk.CTkFont(family="Consolas", size=12))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        guide_text = """INSTALACJA AGENTA OUTLOOK

1. Otwórz terminal/cmd jako Administrator

2. Aktywuj środowisko wirtualne:
   venv\\Scripts\\activate

3. Zainstaluj pywin32:
   pip install pywin32

4. Uruchom post-install:
   python venv\\Scripts\\pywin32_postinstall.py -install

5. Zrestartuj aplikację

WYMAGANIA:
- Windows 10/11
- Microsoft Outlook zainstalowany lokalnie
- Python 3.11+

ROZWIĄZYWANIE PROBLEMÓW:

Jeśli instalacja nie działa:
1. pip install --upgrade pip
2. pip install pypiwin32

Alternatywnie:
- Pobierz wheel z: https://pypi.org/project/pywin32/
- pip install pywin32-XXX.whl

Uwaga: Agent Outlook działa tylko na Windows
z zainstalowanym Microsoft Outlook."""
        
        text.insert("1.0", guide_text)
        text.configure(state="disabled")
        
        ctk.CTkButton(
            guide_window,
            text="Zamknij",
            command=guide_window.destroy
        ).pack(pady=10)
    
    def show_about(self):
        """Show about dialog"""
        about_window = ctk.CTkToplevel(self)
        about_window.title("O systemie")
        about_window.geometry("700x500")
        
        # Center window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - 350
        y = (about_window.winfo_screenheight() // 2) - 250
        about_window.geometry(f"+{x}+{y}")
        
        # Header
        header_frame = ctk.CTkFrame(about_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="🏭 System Zarządzania Produkcją",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="Laser / Prasa Krawędziowa",
            font=ctk.CTkFont(size=16)
        ).pack()
        
        # Version info
        info_frame = ctk.CTkFrame(about_window)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        info_text = f"""
📌 WERSJA: 1.1 Zintegrowana

✅ FAZA 1 - Zarządzanie zamówieniami
   • Rejestracja zamówień i klientów
   • Automatyczna numeracja procesowa
   • System statusów z historią
   • Dashboard SLA z alertami
   • Eksport do Excel, Word, PDF

✅ FAZA 2 - Moduł ofertowania
   • Tworzenie ofert cenowych
   • Kalkulacja marży
   • Konwersja oferta → zamówienie
   • Generowanie PDF
   • Śledzenie statusów ofert

✅ FAZA 3 - Agent Outlook
   • Automatyczne przetwarzanie emaili
   • Rozpoznawanie zapytań i zamówień
   • Ekstraktowanie załączników
   • Automatyczne potwierdzenia
   • Alerty SLA

📊 TECHNOLOGIE:
   • Python 3.11+
   • CustomTkinter (Modern GUI)
   • Supabase (PostgreSQL + Storage)
   • Matplotlib (Wykresy)
   • ReportLab (PDF)
   • Win32com (Outlook)

👨‍💻 ZESPÓŁ:
   Production IT Team
   © 2025 - Wszelkie prawa zastrzeżone

📞 WSPARCIE:
   Email: support@production.local
   Tel: wew. 123
        """
        
        text_widget = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        text_widget.pack(padx=20, pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(about_window)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📖 Dokumentacja",
            width=150,
            command=lambda: self.open_documentation()
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🔧 Diagnostyka",
            width=150,
            command=self.run_diagnostics
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Zamknij",
            width=150,
            command=about_window.destroy
        ).pack(side="right", padx=10)
    
    def open_documentation(self):
        """Open documentation file"""
        import webbrowser
        doc_path = Path("PROJECT_DOCUMENTATION_2025.md")
        if doc_path.exists():
            webbrowser.open(str(doc_path.absolute()))
        else:
            messagebox.showinfo("Info", "Dokumentacja znajduje się w pliku:\nPROJECT_DOCUMENTATION_2025.md")
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        diag_window = ctk.CTkToplevel(self)
        diag_window.title("Diagnostyka systemu")
        diag_window.geometry("600x400")
        
        # Center
        diag_window.update_idletasks()
        x = (diag_window.winfo_screenwidth() // 2) - 300
        y = (diag_window.winfo_screenheight() // 2) - 200
        diag_window.geometry(f"+{x}+{y}")
        
        # Run checks
        results = []
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        results.append(f"✅ Python: {python_version}")
        
        # Check database connection
        try:
            customers = self.db.get_customers()
            results.append(f"✅ Baza danych: Połączono ({len(customers)} klientów)")
        except:
            results.append("❌ Baza danych: Błąd połączenia")
        
        # Check required modules
        modules = {
            'customtkinter': 'CustomTkinter',
            'supabase': 'Supabase',
            'pandas': 'Pandas',
            'openpyxl': 'OpenPyXL',
            'docx': 'Python-docx',
            'reportlab': 'ReportLab',
            'matplotlib': 'Matplotlib',
            'PIL': 'Pillow',
            'tkcalendar': 'TkCalendar'
        }
        
        for module, name in modules.items():
            try:
                __import__(module)
                results.append(f"✅ {name}: Zainstalowany")
            except ImportError:
                results.append(f"❌ {name}: Brak")
        
        # Check Outlook
        if OUTLOOK_AVAILABLE:
            try:
                import win32com.client
                outlook = win32com.client.Dispatch("Outlook.Application")
                results.append("✅ Outlook: Dostępny")
            except:
                results.append("⚠️ Outlook: Zainstalowany ale niedostępny")
        else:
            results.append("❌ pywin32: Niezainstalowany")
        
        # Check environment file
        if Path(".env").exists():
            results.append("✅ Plik .env: Znaleziony")
        else:
            results.append("❌ Plik .env: Brak")
        
        # Display results
        text = ctk.CTkTextbox(diag_window, font=ctk.CTkFont(family="Consolas", size=12))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        text.insert("1.0", "DIAGNOSTYKA SYSTEMU\n" + "="*50 + "\n\n")
        for result in results:
            text.insert("end", result + "\n")
        
        text.configure(state="disabled")
        
        ctk.CTkButton(
            diag_window,
            text="Zamknij",
            command=diag_window.destroy
        ).pack(pady=10)

def main():
    """Main entry point for integrated system"""
    try:
        # Check for .env file
        if not Path(".env").exists() and Path(".env.example").exists():
            result = messagebox.askyesno(
                "Konfiguracja",
                "Nie znaleziono pliku .env\n\n"
                "Czy chcesz skopiować .env.example jako .env?\n"
                "(Będziesz musiał uzupełnić dane Supabase)"
            )
            
            if result:
                import shutil
                shutil.copy(".env.example", ".env")
                messagebox.showinfo(
                    "Info",
                    "Plik .env został utworzony.\n"
                    "Uzupełnij dane dostępu do Supabase przed uruchomieniem."
                )
                return
        
        # Launch integrated application
        app = IntegratedManufacturingSystem()
        
        # Show startup message
        app.after(1000, lambda: app.status_label.configure(
            text="System gotowy | Wszystkie moduły załadowane | Wersja 1.1 Zintegrowana"
        ))
        
        app.mainloop()
        
    except Exception as e:
        messagebox.showerror(
            "Błąd krytyczny",
            f"Nie można uruchomić systemu:\n{e}\n\n"
            "Sprawdź:\n"
            "1. Czy plik .env jest skonfigurowany\n"
            "2. Czy wszystkie zależności są zainstalowane\n"
            "3. Czy masz połączenie z internetem"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
