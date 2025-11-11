#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zintegrowany moduł podglądu 2D/3D i generowania miniatur V3
- Poprawione zarządzanie plikami binarnymi
- Bez lokalnych ścieżek - wszystko w bazie
"""

import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from tkinter import messagebox
import tkinter as tk

# Dodaj mfgviewer do ścieżki
mfgviewer_path = os.path.join(os.path.dirname(__file__), 'mfgviewer')
if mfgviewer_path not in sys.path:
    sys.path.insert(0, mfgviewer_path)

import customtkinter as ctk
import subprocess
import shutil

# Qt imports
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPixmap, QPainter, QImage, QWindow
    HAS_QT = True
except ImportError:
    HAS_QT = False
    print("Warning: PySide6 not installed - viewer features limited")

# Import z mfgviewer
try:
    from mfgviewer.dxf_preview import DxfCanvas, preview_file_2d, SUPPORTED_2D
    from mfgviewer.backend_vtk import VtkViewerWidget, SUPPORTED_3D
    HAS_VIEWERS = True
except ImportError as e:
    print(f"Warning: Cannot import viewers: {e}")
    HAS_VIEWERS = False
    SUPPORTED_2D = ('.dxf', '.dwg')
    SUPPORTED_3D = ('.step', '.stp', '.iges', '.igs', '.stl')


def convert_dwg_to_dxf(dwg_path: str, dxf_path: str) -> bool:
    """Konwertuj plik DWG do DXF używając ODA File Converter"""
    # Ścieżki do ODA File Converter
    oda_paths = [
        r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
        r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
        r"C:\Program Files\ODA\ODAFileConverter 25.6.0\ODAFileConverter.exe",
    ]

    oda_exe = None
    for path in oda_paths:
        if os.path.exists(path):
            oda_exe = path
            break

    if not oda_exe:
        print("ODA File Converter not found. Install from: https://www.opendesign.com/guestfiles/oda_file_converter")
        return False

    try:
        # ODA wymaga folderów nie plików
        input_folder = os.path.dirname(dwg_path)
        output_folder = os.path.dirname(dxf_path)

        # Parametry: input_folder output_folder output_version output_type recursive
        cmd = [
            oda_exe,
            input_folder,
            output_folder,
            "ACAD2018",
            "DXF",
            "0",  # nie rekurencyjnie
            "1"   # audit
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Sprawdź czy plik został utworzony
        expected_dxf = os.path.join(output_folder, Path(dwg_path).stem + ".dxf")
        if os.path.exists(expected_dxf):
            # Przenieś do docelowej lokalizacji jeśli inna
            if expected_dxf != dxf_path:
                shutil.move(expected_dxf, dxf_path)
            return True

        print(f"DWG conversion failed: {result.stderr}")
        return False

    except Exception as e:
        print(f"Error converting DWG to DXF: {e}")
        return False


class ThumbnailGenerator:
    """Generator miniatur dla plików CAD i obrazów"""

    @staticmethod
    def create_placeholder(size: Tuple[int, int], text: str = "N/A") -> bytes:
        """Utwórz placeholder image"""
        img = Image.new('RGB', size, color='#f0f0f0')
        draw = ImageDraw.Draw(img)

        # Dodaj tekst
        try:
            # Spróbuj użyć lepszej czcionki
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = None

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
        draw.text(position, text, fill='#999999', font=font)

        # Dodaj ramkę
        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline='#cccccc')

        # Konwertuj na bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()

    @staticmethod
    def generate_from_image(image_path: str, size: Tuple[int, int] = (200, 200)) -> bytes:
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
    def generate_from_2d_cad(cad_path: str, size: Tuple[int, int] = (200, 200)) -> bytes:
        """Generuj miniaturę z pliku DXF/DWG używając matplotlib"""
        if not HAS_VIEWERS:
            return ThumbnailGenerator.create_placeholder(size, "2D")

        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg

            # Konwersja DWG jeśli potrzebna
            file_to_load = cad_path
            if Path(cad_path).suffix.lower() == '.dwg':
                temp_dxf = tempfile.mktemp(suffix='.dxf')
                if convert_dwg_to_dxf(cad_path, temp_dxf):
                    file_to_load = temp_dxf
                else:
                    return ThumbnailGenerator.create_placeholder(size, "DWG")

            # Utwórz figure matplotlib
            fig = Figure(figsize=(size[0]/100, size[1]/100), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            # Użyj preview_file_2d z mfgviewer
            preview_file_2d(Path(file_to_load), ax, show_bbox=False)

            # Renderuj do bufora
            canvas = FigureCanvasAgg(fig)
            canvas.draw()

            # Pobierz obraz
            buffer = io.BytesIO()
            canvas.print_jpg(buffer)
            return buffer.getvalue()

        except Exception as e:
            print(f"Error generating thumbnail from 2D CAD: {e}")
            ext = Path(cad_path).suffix.upper()[1:]
            return ThumbnailGenerator.create_placeholder(size, ext)

    @staticmethod
    def generate_from_3d_cad(cad_path: str, size: Tuple[int, int] = (200, 200)) -> bytes:
        """Generuj miniaturę z pliku STEP/STL"""
        # Dla uproszczenia, zwróć placeholder
        # Pełna implementacja wymagałaby VTK lub FreeCAD
        ext = Path(cad_path).suffix.upper()[1:]
        return ThumbnailGenerator.create_placeholder(size, f"3D {ext}")


class EnhancedFilePreviewFrame(ctk.CTkFrame):
    """Ramka z podglądem pliku i wyborem źródła grafiki - V3"""

    def __init__(self, parent, title: str, file_types: list, radio_var: tk.StringVar, radio_value: str):
        super().__init__(parent)

        self.title = title
        self.file_types = file_types
        self.radio_var = radio_var
        self.radio_value = radio_value

        # Dane pliku
        self.file_binary = None  # Zawartość binarna pliku
        self.file_name = None    # Nazwa pliku (bez ścieżki)
        self.thumbnail_data = None
        self.preview_4k_data = None

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
            width=220,
            height=220,
            fg_color="gray95"
        )
        self.preview_label.pack(pady=5)

        # Pokaż placeholder
        self.show_placeholder()

        # Przyciski
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        ctk.CTkButton(
            btn_frame,
            text="📁 Wczytaj",
            width=80,
            command=self.load_file
        ).pack(side="left", padx=2)

        self.preview_button = ctk.CTkButton(
            btn_frame,
            text="👁️ Podgląd",
            width=80,
            command=self.show_preview,
            state="disabled"
        )
        self.preview_button.pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="❌ Usuń",
            width=70,
            command=self.clear_file,
            fg_color="#f44336"
        ).pack(side="left", padx=2)

        # Radio button
        self.radio_button = ctk.CTkRadioButton(
            self,
            text="Użyj jako źródło",
            variable=self.radio_var,
            value=self.radio_value
        )
        self.radio_button.pack(pady=5)

        # Label z nazwą pliku
        self.file_label = ctk.CTkLabel(
            self,
            text="Brak pliku",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.file_label.pack(pady=2)

    def show_placeholder(self):
        """Pokaż placeholder"""
        placeholder = ThumbnailGenerator.create_placeholder((200, 200), self.radio_value)
        img = Image.open(io.BytesIO(placeholder))
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=photo, text="")
        self.preview_label.image = photo

    def load_file(self):
        """Załaduj plik i zapisz go binarnie"""
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
            try:
                # Odczytaj plik jako dane binarne
                with open(file_path, 'rb') as f:
                    self.file_binary = f.read()

                # Zapisz nazwę pliku (bez ścieżki)
                self.file_name = Path(file_path).name

                # Aktualizuj UI
                self.file_label.configure(text=self.file_name)
                self.preview_button.configure(state="normal")

                # Generuj miniaturę z pliku tymczasowego
                self.generate_and_display_thumbnail(file_path)

                # Automatycznie wybierz to źródło
                self.radio_var.set(self.radio_value)

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można wczytać pliku:\n{e}")

    def generate_and_display_thumbnail(self, temp_path: str = None):
        """Generuj i wyświetl miniaturę"""
        if not self.file_binary:
            return

        try:
            # Jeśli nie mamy temp_path, utwórz plik tymczasowy
            if not temp_path:
                ext = Path(self.file_name).suffix if self.file_name else '.tmp'
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(self.file_binary)
                    temp_path = tmp.name

            # Generuj miniaturę
            ext = Path(self.file_name).suffix.lower()

            if ext in SUPPORTED_2D:
                self.thumbnail_data = ThumbnailGenerator.generate_from_2d_cad(temp_path)
            elif ext in SUPPORTED_3D:
                self.thumbnail_data = ThumbnailGenerator.generate_from_3d_cad(temp_path)
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                self.thumbnail_data = ThumbnailGenerator.generate_from_image(temp_path)
            else:
                self.thumbnail_data = ThumbnailGenerator.create_placeholder((200, 200), ext.upper()[1:])

            # Usuń plik tymczasowy jeśli go utworzyliśmy
            if not temp_path or temp_path.startswith(tempfile.gettempdir()):
                try:
                    os.unlink(temp_path)
                except:
                    pass

            # Wyświetl miniaturę
            if self.thumbnail_data:
                img = Image.open(io.BytesIO(self.thumbnail_data))
                from PIL import ImageTk
                photo = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo

        except Exception as e:
            print(f"Błąd generowania miniatury: {e}")
            self.show_placeholder()

    def show_preview(self):
        """Pokaż podgląd w oknie popup"""
        if self.file_binary:
            # Utwórz tymczasowy plik do podglądu
            ext = Path(self.file_name).suffix if self.file_name else '.tmp'
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(self.file_binary)
                temp_path = tmp.name

            # Otwórz w domyślnej aplikacji
            try:
                os.startfile(temp_path)
            except:
                messagebox.showinfo("Info", f"Plik zapisany tymczasowo:\n{temp_path}")

    def clear_file(self):
        """Wyczyść wczytany plik"""
        self.file_binary = None
        self.file_name = None
        self.thumbnail_data = None
        self.preview_4k_data = None

        self.file_label.configure(text="Brak pliku")
        self.preview_button.configure(state="disabled")
        self.show_placeholder()

        # Jeśli to było wybrane źródło, wyczyść wybór
        if self.radio_var.get() == self.radio_value:
            self.radio_var.set("")

    def get_file_binary(self) -> Optional[bytes]:
        """Zwróć dane binarne pliku"""
        return self.file_binary

    def get_file_name(self) -> Optional[str]:
        """Zwróć nazwę pliku"""
        return self.file_name

    def get_thumbnail(self) -> Optional[bytes]:
        """Zwróć dane miniatury"""
        return self.thumbnail_data

    def set_file_data(self, file_binary: bytes, file_name: str):
        """Ustaw dane pliku (np. przy wczytywaniu z bazy)"""
        self.file_binary = file_binary
        self.file_name = file_name
        self.file_label.configure(text=file_name)
        self.preview_button.configure(state="normal")

        # Generuj miniaturę
        self.generate_and_display_thumbnail()


def test_viewer():
    """Test widoku"""
    root = ctk.CTk()
    root.geometry("800x600")

    radio_var = tk.StringVar()

    frame = EnhancedFilePreviewFrame(
        root,
        "Test File",
        ['.dxf', '.dwg', '.step', '.jpg'],
        radio_var,
        "TEST"
    )
    frame.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    test_viewer()