#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zintegrowany moduł podglądu 2D/3D i generowania miniatur
Wykorzystuje kod z mfgviewer do podglądu plików CAD
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
import io

# Dodaj mfgviewer do ścieżki
mfgviewer_path = os.path.join(os.path.dirname(__file__), 'mfgviewer')
if mfgviewer_path not in sys.path:
    sys.path.insert(0, mfgviewer_path)

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

# Import z mfgviewer
try:
    from mfgviewer.dxf_preview import DxfViewer, SUPPORTED_2D
    from mfgviewer.backend_vtk import VtkViewerWidget, SUPPORTED_3D
    HAS_VIEWERS = True
except ImportError as e:
    print(f"Warning: Cannot import viewers: {e}")
    HAS_VIEWERS = False
    SUPPORTED_2D = ('.dxf', '.dwg')
    SUPPORTED_3D = ('.step', '.stp', '.iges', '.igs', '.stl')

# Qt imports dla VTK
try:
    from PySide6 import QtWidgets, QtCore
    from PySide6.QtGui import QPixmap, QPainter, QImage
    HAS_QT = True
except ImportError:
    HAS_QT = False


class ThumbnailGenerator:
    """Generator miniatur dla plików CAD i obrazów"""

    @staticmethod
    def generate_from_image(image_path: str, size: Tuple[int, int] = (100, 100)) -> bytes:
        """Generuj miniaturę z pliku graficznego"""
        try:
            img = Image.open(image_path)
            # Zachowaj proporcje
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Utwórz białe tło
            background = Image.new('RGB', size, (255, 255, 255))

            # Wycentruj obraz
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            if img.mode == 'RGBA':
                background.paste(img, offset, img)
            else:
                background.paste(img, offset)

            # Zapisz do bytes
            buffer = io.BytesIO()
            background.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()

        except Exception as e:
            print(f"Error generating thumbnail from image: {e}")
            return ThumbnailGenerator.create_placeholder(size, "IMG")

    @staticmethod
    def generate_from_2d_cad(cad_path: str, size: Tuple[int, int] = (100, 100)) -> bytes:
        """Generuj miniaturę z pliku DXF/DWG"""
        if not HAS_VIEWERS:
            return ThumbnailGenerator.create_placeholder(size, "2D")

        try:
            # TODO: Implementacja używająca DxfViewer do renderowania
            # Na razie zwraca placeholder
            ext = Path(cad_path).suffix.upper()[1:]
            return ThumbnailGenerator.create_placeholder(size, ext)

        except Exception as e:
            print(f"Error generating thumbnail from 2D CAD: {e}")
            return ThumbnailGenerator.create_placeholder(size, "2D")

    @staticmethod
    def generate_from_3d_cad(cad_path: str, size: Tuple[int, int] = (100, 100)) -> bytes:
        """Generuj miniaturę z pliku STEP/STL"""
        if not HAS_VIEWERS or not HAS_QT:
            return ThumbnailGenerator.create_placeholder(size, "3D")

        try:
            # TODO: Implementacja używająca VtkViewerWidget do renderowania
            # Na razie zwraca placeholder
            ext = Path(cad_path).suffix.upper()[1:]
            return ThumbnailGenerator.create_placeholder(size, ext)

        except Exception as e:
            print(f"Error generating thumbnail from 3D CAD: {e}")
            return ThumbnailGenerator.create_placeholder(size, "3D")

    @staticmethod
    def create_placeholder(size: Tuple[int, int], text: str = "N/A") -> bytes:
        """Utwórz placeholder gdy nie można wygenerować miniatury"""
        img = Image.new('RGB', size, (240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Ramka
        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline=(200, 200, 200), width=1)

        # Tekst
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
        draw.text(position, text, fill=(150, 150, 150), font=font)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()


class ViewerPopup(ctk.CTkToplevel):
    """Okno popup do podglądu plików CAD"""

    def __init__(self, parent, file_path: str):
        super().__init__(parent)
        self.file_path = file_path
        self.file_ext = Path(file_path).suffix.lower()

        # Ustaw tytuł i rozmiar
        self.title(f"Podgląd: {Path(file_path).name}")
        self.geometry("800x600")

        # Uczyń okno modalnym
        self.transient(parent)
        self.grab_set()

        # Centruj okno
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 400
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.load_file()

    def setup_ui(self):
        """Ustaw interfejs użytkownika"""
        # Nagłówek
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text=f"📁 {Path(self.file_path).name}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            header,
            text="Zamknij",
            width=100,
            command=self.destroy
        ).pack(side="right", padx=10)

        # Kontener na viewer
        self.viewer_frame = ctk.CTkFrame(self)
        self.viewer_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Loading label
        self.loading_label = ctk.CTkLabel(
            self.viewer_frame,
            text="Ładowanie podglądu...",
            font=ctk.CTkFont(size=14)
        )
        self.loading_label.pack(expand=True)

    def load_file(self):
        """Załaduj plik do odpowiedniego viewera"""
        if not HAS_VIEWERS:
            self.show_error("Moduły podglądu nie są dostępne")
            return

        try:
            if self.file_ext in SUPPORTED_2D:
                self.load_2d_file()
            elif self.file_ext in SUPPORTED_3D:
                self.load_3d_file()
            else:
                self.show_error(f"Nieobsługiwany format pliku: {self.file_ext}")
        except Exception as e:
            self.show_error(f"Błąd ładowania pliku:\n{str(e)}")

    def load_2d_file(self):
        """Załaduj plik 2D (DXF/DWG)"""
        if not HAS_QT:
            self.show_error("PySide6 nie jest zainstalowane")
            return

        # Ukryj loading label
        self.loading_label.pack_forget()

        # Utwórz aplikację Qt jeśli nie istnieje
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        # Utwórz widget DXF viewer
        self.viewer = DxfViewer()

        # Osadź widget Qt w Tkinter
        # TODO: Implementacja osadzania Qt w Tkinter
        self.show_error("Podgląd 2D w przygotowaniu")

    def load_3d_file(self):
        """Załaduj plik 3D (STEP/STL)"""
        if not HAS_QT:
            self.show_error("PySide6 nie jest zainstalowane")
            return

        # Ukryj loading label
        self.loading_label.pack_forget()

        # Utwórz aplikację Qt jeśli nie istnieje
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        # Utwórz widget VTK viewer
        self.viewer = VtkViewerWidget()

        # Osadź widget Qt w Tkinter
        # TODO: Implementacja osadzania Qt w Tkinter
        self.show_error("Podgląd 3D w przygotowaniu")

    def show_error(self, message: str):
        """Pokaż komunikat o błędzie"""
        self.loading_label.configure(
            text=f"❌ {message}",
            text_color="red"
        )


class EnhancedFilePreviewFrame(ctk.CTkFrame):
    """Ramka z podglądem pliku i wyborem źródła grafiki"""

    def __init__(self, parent, title: str, file_types: list, radio_var: tk.StringVar, radio_value: str):
        super().__init__(parent)

        self.title = title
        self.file_types = file_types
        self.radio_var = radio_var
        self.radio_value = radio_value
        self.file_path = None
        self.thumbnail_data = None

        self.setup_ui()

    def setup_ui(self):
        """Ustaw interfejs użytkownika"""
        # Tytuł
        ctk.CTkLabel(
            self,
            text=self.title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)

        # Podgląd
        self.preview_label = ctk.CTkLabel(
            self,
            text="",
            width=200,
            height=200,
            fg_color="gray95"
        )
        self.preview_label.pack(pady=5)

        # Przyciski
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        ctk.CTkButton(
            btn_frame,
            text="📁 Wczytaj",
            width=100,
            command=self.load_file
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="👁️ Podgląd",
            width=100,
            command=self.show_preview,
            state="disabled"
        ).pack(side="left", padx=2)

        self.preview_button = btn_frame.winfo_children()[1]

        # Radio button
        self.radio = ctk.CTkRadioButton(
            self,
            text="Użyj jako główną grafikę",
            variable=self.radio_var,
            value=self.radio_value
        )
        self.radio.pack(pady=5)

        # Info o pliku
        self.file_label = ctk.CTkLabel(
            self,
            text="Brak pliku",
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        self.file_label.pack()

    def load_file(self):
        """Załaduj plik"""
        from tkinter import filedialog

        # Przygotuj filtry plików
        filetypes = [("Obsługiwane pliki", " ".join(f"*{ext}" for ext in self.file_types))]
        for ext in self.file_types:
            filetypes.append((f"Pliki {ext.upper()}", f"*{ext}"))

        file_path = filedialog.askopenfilename(
            title=f"Wybierz plik {self.title}",
            filetypes=filetypes
        )

        if file_path:
            self.file_path = file_path
            self.file_label.configure(text=Path(file_path).name)
            self.preview_button.configure(state="normal")

            # Generuj miniaturę
            self.generate_thumbnail()

            # Automatycznie wybierz to źródło
            self.radio_var.set(self.radio_value)

    def generate_thumbnail(self):
        """Generuj miniaturę pliku"""
        if not self.file_path:
            return

        ext = Path(self.file_path).suffix.lower()

        if ext in SUPPORTED_2D:
            self.thumbnail_data = ThumbnailGenerator.generate_from_2d_cad(self.file_path)
        elif ext in SUPPORTED_3D:
            self.thumbnail_data = ThumbnailGenerator.generate_from_3d_cad(self.file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            self.thumbnail_data = ThumbnailGenerator.generate_from_image(self.file_path)
        else:
            self.thumbnail_data = ThumbnailGenerator.create_placeholder((100, 100), ext.upper()[1:])

        # TODO: Wyświetl miniaturę w preview_label

    def show_preview(self):
        """Pokaż podgląd w oknie popup"""
        if self.file_path and os.path.exists(self.file_path):
            ViewerPopup(self, self.file_path)

    def get_file_path(self) -> Optional[str]:
        """Zwróć ścieżkę do pliku"""
        return self.file_path

    def get_thumbnail(self) -> Optional[bytes]:
        """Zwróć dane miniatury"""
        return self.thumbnail_data


def test_viewer():
    """Test viewera"""
    root = ctk.CTk()
    root.title("Test Integrated Viewer")
    root.geometry("900x500")

    # Radio variable
    source_var = tk.StringVar(value="2D")

    # Frame container
    container = ctk.CTkFrame(root)
    container.pack(fill="both", expand=True, padx=20, pady=20)

    # 2D Preview
    frame_2d = EnhancedFilePreviewFrame(
        container,
        "Plik 2D (DXF/DWG)",
        ['.dxf', '.dwg'],
        source_var,
        "2D"
    )
    frame_2d.pack(side="left", padx=10, fill="y")

    # 3D Preview
    frame_3d = EnhancedFilePreviewFrame(
        container,
        "Plik 3D (STEP/STL)",
        ['.step', '.stp', '.iges', '.igs', '.stl'],
        source_var,
        "3D"
    )
    frame_3d.pack(side="left", padx=10, fill="y")

    # User image
    frame_img = EnhancedFilePreviewFrame(
        container,
        "Grafika użytkownika",
        ['.jpg', '.jpeg', '.png', '.bmp', '.gif'],
        source_var,
        "USER"
    )
    frame_img.pack(side="left", padx=10, fill="y")

    # Status
    status = ctk.CTkLabel(root, text="")
    status.pack(pady=10)

    def update_status(*args):
        status.configure(text=f"Wybrane źródło: {source_var.get()}")

    source_var.trace('w', update_status)

    root.mainloop()


if __name__ == "__main__":
    test_viewer()