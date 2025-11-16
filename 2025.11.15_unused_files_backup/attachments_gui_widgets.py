#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attachments GUI Widgets
Gotowe widgety GUI do obsługi załączników w dialogach ofert i zamówień
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
import os
import tempfile
import subprocess
import platform

from attachments_manager import AttachmentsManager, format_file_size, get_file_icon_by_type


class AttachmentsWidget(ctk.CTkFrame):
    """
    Widget do zarządzania załącznikami w dialogu oferty/zamówienia
    Można łatwo dodać do istniejących dialogów
    """

    def __init__(
        self,
        parent,
        db_client,
        entity_type: str,  # 'order' lub 'quotation'
        entity_id: str = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.db_client = db_client
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.attachments_manager = AttachmentsManager(db_client)

        self.setup_ui()

        # Załaduj załączniki jeśli entity_id jest podane
        if self.entity_id:
            self.load_attachments()

    def setup_ui(self):
        """Tworzy interfejs widgetu załączników"""

        # Nagłówek
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            header_frame,
            text="📎 Załączniki",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)

        # Przyciski
        btn_frame = ctk.CTkFrame(header_frame)
        btn_frame.pack(side="right", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="➕ Dodaj pliki",
            width=120,
            command=self.add_files,
            fg_color="#4CAF50"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="👁️ Podgląd",
            width=100,
            command=self.preview_file
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="💾 Pobierz",
            width=100,
            command=self.download_file
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Usuń",
            width=80,
            command=self.delete_attachment,
            fg_color="#DC143C"
        ).pack(side="left", padx=5)

        # Lista załączników
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview dla listy załączników
        self.tree = ttk.Treeview(
            list_frame,
            columns=('files', 'size', 'date', 'notes'),
            show='headings',
            height=5
        )

        self.tree.heading('files', text='Pliki')
        self.tree.heading('size', text='Rozmiar')
        self.tree.heading('date', text='Data dodania')
        self.tree.heading('notes', text='Notatki')

        self.tree.column('files', width=250)
        self.tree.column('size', width=100)
        self.tree.column('date', width=150)
        self.tree.column('notes', width=200)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind podwójne kliknięcie do podglądu
        self.tree.bind("<Double-1>", lambda e: self.preview_file())

        # Info label
        self.info_label = ctk.CTkLabel(
            self,
            text="Brak załączników",
            font=ctk.CTkFont(size=11)
        )
        self.info_label.pack(pady=5)

        # Styl dla treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#212121", foreground="white",
                       fieldbackground="#212121", borderwidth=0)
        style.configure("Treeview.Heading", background="#313131", foreground="white")
        style.map('Treeview', background=[('selected', '#144870')])

    def set_entity_id(self, entity_id: str):
        """
        Ustawia entity_id i ładuje załączniki

        Args:
            entity_id: ID zamówienia lub oferty
        """
        self.entity_id = entity_id
        self.load_attachments()

    def load_attachments(self):
        """Ładuje listę załączników z bazy"""
        if not self.entity_id:
            return

        # Wyczyść listę
        self.tree.delete(*self.tree.get_children())

        # Pobierz załączniki
        attachments = self.attachments_manager.get_attachments_list(
            self.entity_type,
            self.entity_id
        )

        # Dodaj do listy
        for attachment in attachments:
            # Formatuj listę plików
            files_list = ", ".join([f['filename'] for f in attachment.files_metadata])

            # Formatuj rozmiar
            size_str = format_file_size(attachment.total_size)

            # Formatuj datę
            date_str = attachment.created_at[:10] if attachment.created_at else ''

            self.tree.insert('', 'end',
                           values=(
                               files_list,
                               size_str,
                               date_str,
                               attachment.notes or ''
                           ),
                           tags=(attachment.id,))

        # Aktualizuj info label
        if attachments:
            summary = self.attachments_manager.get_attachment_size_summary(
                self.entity_type,
                self.entity_id
            )
            info_text = f"{summary['files_count']} plików w {summary['attachments_count']} archiwach | "
            info_text += f"Razem: {format_file_size(summary['total_size'])}"
            self.info_label.configure(text=info_text)
        else:
            self.info_label.configure(text="Brak załączników")

    def add_files(self):
        """Dodaje pliki jako załącznik"""
        if not self.entity_id:
            messagebox.showwarning(
                "Uwaga",
                "Zapisz najpierw dokument, aby móc dodawać załączniki"
            )
            return

        # Dialog wyboru plików
        file_paths = filedialog.askopenfilenames(
            title="Wybierz pliki do dodania",
            filetypes=[
                ("Wszystkie pliki", "*.*"),
                ("PDF", "*.pdf"),
                ("Word", "*.doc;*.docx"),
                ("Excel", "*.xls;*.xlsx"),
                ("Obrazy", "*.png;*.jpg;*.jpeg;*.gif"),
                ("CAD", "*.dxf;*.dwg;*.step;*.stp")
            ]
        )

        if not file_paths:
            return

        # Poproś o notatki (opcjonalne)
        notes = self.ask_notes()

        # Dodaj pliki
        result = self.attachments_manager.add_files(
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            file_paths=list(file_paths),
            notes=notes
        )

        if result:
            messagebox.showinfo("Sukces", f"Dodano {len(file_paths)} plików jako załącznik")
            self.load_attachments()
        else:
            messagebox.showerror("Błąd", "Nie udało się dodać załączników")

    def preview_file(self):
        """Podgląd wybranego pliku"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz załącznik do podglądu")
            return

        # Pobierz ID załącznika
        item = self.tree.item(selection[0])
        attachment_id = item['tags'][0]

        # Pobierz listę plików w załączniku
        files_list = self.attachments_manager.get_files_list(attachment_id)

        if not files_list:
            messagebox.showwarning("Uwaga", "Brak plików w załączniku")
            return

        # Jeśli jest tylko jeden plik, otwórz go od razu
        if len(files_list) == 1:
            self._open_file(attachment_id, files_list[0].filename)
            return

        # Jeśli jest więcej plików, pokaż dialog wyboru
        file_selection_dialog = FileSelectionDialog(
            self,
            files_list,
            lambda filename: self._open_file(attachment_id, filename)
        )
        file_selection_dialog.focus()

    def download_file(self):
        """Pobiera (eksportuje) wybrany plik"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz załącznik do pobrania")
            return

        # Pobierz ID załącznika
        item = self.tree.item(selection[0])
        attachment_id = item['tags'][0]

        # Pobierz listę plików
        files_list = self.attachments_manager.get_files_list(attachment_id)

        if not files_list:
            messagebox.showwarning("Uwaga", "Brak plików w załączniku")
            return

        # Jeśli jest tylko jeden plik, zapisz go od razu
        if len(files_list) == 1:
            self._download_single_file(attachment_id, files_list[0].filename)
            return

        # Jeśli jest więcej plików, rozpakuj wszystkie
        temp_dir = self.attachments_manager.extract_all_to_temp(attachment_id)
        if temp_dir:
            # Otwórz folder w eksploratorze
            self._open_folder(temp_dir)
            messagebox.showinfo(
                "Sukces",
                f"Rozpakowano {len(files_list)} plików do:\n{temp_dir}\n\n"
                "Folder tymczasowy zostanie usunięty po zamknięciu aplikacji."
            )

    def delete_attachment(self):
        """Usuwa wybrany załącznik"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz załącznik do usunięcia")
            return

        # Potwierdź usunięcie
        if not messagebox.askyesno("Potwierdzenie", "Czy na pewno usunąć załącznik?"):
            return

        # Pobierz ID załącznika
        item = self.tree.item(selection[0])
        attachment_id = item['tags'][0]

        # Usuń załącznik
        if self.attachments_manager.delete_attachment(attachment_id):
            messagebox.showinfo("Sukces", "Załącznik został usunięty")
            self.load_attachments()
        else:
            messagebox.showerror("Błąd", "Nie udało się usunąć załącznika")

    def ask_notes(self) -> str:
        """Dialog z pytaniem o notatki do załącznika"""
        dialog = ctk.CTkInputDialog(
            text="Notatki do załącznika (opcjonalne):",
            title="Notatki"
        )
        return dialog.get_input() or ""

    def _open_file(self, attachment_id: str, filename: str):
        """
        Otwiera plik w domyślnej aplikacji

        Args:
            attachment_id: ID załącznika
            filename: Nazwa pliku do otwarcia
        """
        try:
            # Wyodrębnij plik
            file_data = self.attachments_manager.extract_file(attachment_id, filename)
            if not file_data:
                messagebox.showerror("Błąd", f"Nie udało się otworzyć pliku: {filename}")
                return

            # Zapisz do pliku tymczasowego
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(filename)[1],
                prefix=os.path.splitext(filename)[0] + "_"
            )
            temp_file.write(file_data)
            temp_file.close()

            # Otwórz w domyślnej aplikacji
            if platform.system() == 'Windows':
                os.startfile(temp_file.name)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', temp_file.name])
            else:  # Linux
                subprocess.call(['xdg-open', temp_file.name])

            print(f"✅ Otwarto plik: {filename}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć pliku:\n{e}")

    def _download_single_file(self, attachment_id: str, filename: str):
        """
        Pobiera pojedynczy plik

        Args:
            attachment_id: ID załącznika
            filename: Nazwa pliku
        """
        try:
            # Dialog zapisu
            save_path = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(filename)[1],
                initialfile=filename,
                title="Zapisz plik jako"
            )

            if not save_path:
                return

            # Wyodrębnij plik
            file_data = self.attachments_manager.extract_file(attachment_id, filename)
            if not file_data:
                messagebox.showerror("Błąd", "Nie udało się pobrać pliku")
                return

            # Zapisz plik
            with open(save_path, 'wb') as f:
                f.write(file_data)

            messagebox.showinfo("Sukces", f"Plik zapisany:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku:\n{e}")

    def _open_folder(self, folder_path: str):
        """
        Otwiera folder w eksploratorze

        Args:
            folder_path: Ścieżka do folderu
        """
        try:
            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', folder_path])
            else:  # Linux
                subprocess.call(['xdg-open', folder_path])
        except Exception as e:
            print(f"❌ Nie udało się otworzyć folderu: {e}")


class FileSelectionDialog(ctk.CTkToplevel):
    """Dialog wyboru pliku z listy plików w załączniku"""

    def __init__(self, parent, files_list, on_select_callback):
        super().__init__(parent)

        self.files_list = files_list
        self.on_select_callback = on_select_callback

        self.title("Wybierz plik")
        self.geometry("600x400")

        self.transient(parent)
        self.grab_set()

        self.setup_ui()

        # Wyśrodkuj okno
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 300
        y = (self.winfo_screenheight() // 2) - 200
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        """Tworzy interfejs dialogu"""

        # Nagłówek
        header = ctk.CTkLabel(
            self,
            text="Wybierz plik do otwarcia",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=10)

        # Lista plików
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(
            list_frame,
            columns=('icon', 'filename', 'size', 'type'),
            show='headings'
        )

        self.tree.heading('icon', text='')
        self.tree.heading('filename', text='Nazwa pliku')
        self.tree.heading('size', text='Rozmiar')
        self.tree.heading('type', text='Typ')

        self.tree.column('icon', width=30)
        self.tree.column('filename', width=300)
        self.tree.column('size', width=100)
        self.tree.column('type', width=150)

        # Dodaj pliki do listy
        for file_meta in self.files_list:
            icon = get_file_icon_by_type(file_meta.type)
            size_str = format_file_size(file_meta.size)

            self.tree.insert('', 'end',
                           values=(icon, file_meta.filename, size_str, file_meta.type))

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind podwójne kliknięcie
        self.tree.bind("<Double-1>", lambda e: self.select_file())

        # Przyciski
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Otwórz",
            width=150,
            command=self.select_file
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Anuluj",
            width=150,
            command=self.destroy
        ).pack(side="right", padx=10)

    def select_file(self):
        """Wybiera plik i wywołuje callback"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        filename = item['values'][1]

        self.destroy()
        self.on_select_callback(filename)


# Przykład użycia
if __name__ == '__main__':
    print("AttachmentsGUIWidgets - Widgety GUI do zarządzania załącznikami")
    print("=" * 60)
    print("Przykład użycia w dialogu oferty/zamówienia:")
    print("""
    # W __init__ dialogu:
    self.attachments_widget = AttachmentsWidget(
        main_frame,
        db_client=self.db.client,
        entity_type='quotation',  # lub 'order'
        entity_id=None  # ustaw po zapisaniu
    )
    self.attachments_widget.pack(fill="both", expand=True, padx=5, pady=10)

    # Po zapisaniu oferty/zamówienia:
    self.attachments_widget.set_entity_id(saved_id)
    """)
