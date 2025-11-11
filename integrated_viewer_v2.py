#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zintegrowany moduł podglądu 2D/3D i generowania miniatur V2
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
        # ACAD2018 DXF 0 = konwertuj do DXF w formacie AutoCAD 2018
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
        # ODA tworzy plik z tą samą nazwą ale rozszerzeniem .dxf
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


class QtInTk:
    """Helper class to embed Qt widget in Tkinter window"""

    def __init__(self, tk_parent, qt_widget):
        self.tk_parent = tk_parent
        self.qt_widget = qt_widget

        # Get the window ID from tkinter
        self.tk_window_id = self.tk_parent.winfo_id()

        # Create container for Qt widget
        self.container = tk.Frame(self.tk_parent)
        self.container.pack(fill="both", expand=True)

        # Embed Qt widget
        self.embed_qt()

    def embed_qt(self):
        """Embed Qt widget into Tkinter frame"""
        if not HAS_QT:
            return

        # Set Qt widget parent to Tkinter window ID
        window = QWindow.fromWinId(self.container.winfo_id())
        self.qt_widget.show()

        # Create container widget
        container = QWidget.createWindowContainer(window)

        # Size the Qt widget to fit
        self.qt_widget.resize(self.container.winfo_width(), self.container.winfo_height())

        # Bind resize event
        self.container.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """Handle resize events"""
        if self.qt_widget:
            self.qt_widget.resize(event.width, event.height)


class ThumbnailGenerator:
    """Generator miniatur dla plików CAD i obrazów"""

    @staticmethod
    def generate_4k_preview(file_path: str, file_type: str = None) -> bytes:
        """Generuj podgląd 4K (3840x2160) w formacie JPEG"""
        try:
            ext = Path(file_path).suffix.lower()

            # Dla obrazów
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                img = Image.open(file_path)
                # Przeskaluj do 4K zachowując proporcje
                img.thumbnail((3840, 2160), Image.Resampling.LANCZOS)

                # Utwórz białe tło 4K
                background = Image.new('RGB', (3840, 2160), (255, 255, 255))
                # Wycentruj obraz
                offset = ((3840 - img.width) // 2, (2160 - img.height) // 2)
                if img.mode == 'RGBA':
                    background.paste(img, offset, img)
                else:
                    background.paste(img, offset)

                # Zapisz jako JPEG z wysoką jakością
                buffer = io.BytesIO()
                background.save(buffer, format='JPEG', quality=95)
                return buffer.getvalue()

            # Dla DXF/DWG
            elif ext in ['.dxf', '.dwg']:
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_agg import FigureCanvasAgg

                # Utwórz dużą figure dla 4K
                fig = Figure(figsize=(38.4, 21.6), dpi=100, facecolor='white')
                ax = fig.add_subplot(111)

                # Konwersja DWG jeśli potrzebna
                file_to_load = file_path
                if ext == '.dwg':
                    temp_dxf = tempfile.mktemp(suffix='.dxf')
                    if convert_dwg_to_dxf(file_path, temp_dxf):
                        file_to_load = temp_dxf
                    else:
                        return ThumbnailGenerator.create_placeholder((3840, 2160), "DWG")

                # Renderuj
                from mfgviewer.dxf_preview import preview_file_2d
                preview_file_2d(Path(file_to_load), ax, show_bbox=True)

                # Renderuj do bufora
                canvas = FigureCanvasAgg(fig)
                canvas.draw()

                buffer = io.BytesIO()
                canvas.print_jpg(buffer, dpi=100)
                return buffer.getvalue()

            # Dla 3D
            elif ext in ['.step', '.stp', '.stl', '.iges', '.igs']:
                # Używamy tej samej metody co miniatura ale w 4K
                return ThumbnailGenerator.generate_from_3d_cad(file_path, size=(3840, 2160))

            # Fallback
            return ThumbnailGenerator.create_placeholder((3840, 2160), ext.upper()[1:])

        except Exception as e:
            print(f"Error generating 4K preview: {e}")
            return ThumbnailGenerator.create_placeholder((3840, 2160), "ERROR")

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
            fig = Figure(figsize=(size[0]/100, size[1]/100), dpi=100)
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
        """Generuj miniaturę z pliku STEP/STL z off-screen renderingiem"""
        if not HAS_VIEWERS or not HAS_QT:
            return ThumbnailGenerator.create_placeholder(size, "3D")

        try:
            import vtk
            from vtk import vtkWindowToImageFilter, vtkJPEGWriter
            from vtkmodules.vtkIOGeometry import vtkSTLReader
            from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor, vtkPolyDataMapper
            from vtkmodules.vtkFiltersCore import vtkPolyDataNormals, vtkTriangleFilter
            from vtkmodules.vtkCommonColor import vtkNamedColors

            # Konwertuj STEP/IGES do STL jeśli potrzebne
            from mfgviewer.backend_vtk import convert_to_stl
            stl_path = convert_to_stl(str(cad_path))

            # Czytaj STL
            reader = vtkSTLReader()
            reader.SetFileName(stl_path)
            reader.Update()

            # Filtry
            tri = vtkTriangleFilter()
            tri.SetInputConnection(reader.GetOutputPort())
            tri.Update()

            norms = vtkPolyDataNormals()
            norms.SetInputConnection(tri.GetOutputPort())
            norms.SetSplitting(True)
            norms.SetFeatureAngle(30.0)
            norms.Update()

            # Mapper i Actor
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(norms.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)

            # Kolory
            colors = vtkNamedColors()
            actor.GetProperty().SetColor(colors.GetColor3d("LightSteelBlue"))
            actor.GetProperty().SetInterpolationToPhong()

            # Utwórz renderer i render window
            renderer = vtkRenderer()
            renderer.SetBackground(1.0, 1.0, 1.0)  # Białe tło
            renderer.AddActor(actor)

            # Ustaw kamerę na rzut ISO
            camera = renderer.GetActiveCamera()
            camera.SetPosition(1, 1, 1)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
            renderer.ResetCamera()
            camera.Zoom(1.2)

            # Render window (off-screen)
            renderWindow = vtk.vtkRenderWindow()
            renderWindow.SetOffScreenRendering(1)
            renderWindow.AddRenderer(renderer)
            renderWindow.SetSize(size[0], size[1])
            renderWindow.Render()

            # Capture do obrazu
            windowToImageFilter = vtkWindowToImageFilter()
            windowToImageFilter.SetInput(renderWindow)
            windowToImageFilter.SetScale(1)
            windowToImageFilter.SetInputBufferTypeToRGBA()
            windowToImageFilter.ReadFrontBufferOff()
            windowToImageFilter.Update()

            # Zapisz do bufora JPEG
            writer = vtkJPEGWriter()
            writer.SetWriteToMemory(1)
            writer.SetInputConnection(windowToImageFilter.GetOutputPort())
            writer.Write()

            # Pobierz dane
            data = writer.GetResult()
            bytes_data = bytes([data.GetValue(i) for i in range(data.GetNumberOfValues())])

            return bytes_data

        except Exception as e:
            print(f"Error generating thumbnail from 3D CAD: {e}")
            import traceback
            traceback.print_exc()
            ext = Path(cad_path).suffix.upper()[1:]
            return ThumbnailGenerator.create_placeholder(size, ext)

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
        self.qt_app = None
        self.qt_widget = None

        # Ustaw tytuł i rozmiar
        self.title(f"Podgląd: {Path(file_path).name}")

        # Ustaw rozmiar zależnie od typu pliku
        if self.file_ext in SUPPORTED_2D:
            self.geometry("1200x700")
        else:
            self.geometry("900x600")

        # Uczyń okno modalnym
        self.transient(parent)
        self.grab_set()

        # Centruj okno
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.setup_ui()

        # Załaduj plik po krótkim opóźnieniu aby okno się wyrenderowało
        self.after(100, self.load_file)

    def setup_ui(self):
        """Ustaw interfejs użytkownika"""
        # Nagłówek
        header = ctk.CTkFrame(self, height=50)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"📁 {Path(self.file_path).name}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            header,
            text="Zamknij",
            width=100,
            command=self.close_viewer
        ).pack(side="right", padx=10)

        # Kontener na viewer
        self.viewer_frame = tk.Frame(self, bg='black')
        self.viewer_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Loading label
        self.loading_label = ctk.CTkLabel(
            self.viewer_frame,
            text="Ładowanie podglądu...",
            font=ctk.CTkFont(size=14),
            fg_color="black",
            text_color="white"
        )
        self.loading_label.pack(expand=True)

    def load_file(self):
        """Załaduj plik do odpowiedniego viewera"""
        if not os.path.exists(self.file_path):
            self.show_error(f"Plik nie istnieje: {self.file_path}")
            return

        if not HAS_VIEWERS:
            self.show_error("Moduły podglądu nie są dostępne.\nZainstaluj: pip install PySide6 ezdxf matplotlib")
            return

        try:
            if self.file_ext in SUPPORTED_2D:
                self.load_2d_file()
            elif self.file_ext in SUPPORTED_3D:
                self.load_3d_file()
            elif self.file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                self.load_image_file()
            else:
                self.show_error(f"Nieobsługiwany format pliku: {self.file_ext}")
        except Exception as e:
            self.show_error(f"Błąd ładowania pliku:\n{str(e)}\n{traceback.format_exc()}")

    def load_2d_file(self):
        """Załaduj plik 2D (DXF/DWG) używając prostego podejścia z matplotlib"""
        # Ukryj loading label
        self.loading_label.pack_forget()

        # Spróbuj najpierw prostszego podejścia z matplotlib
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            # Jeśli plik to DWG, potrzebujemy konwersji
            file_to_load = self.file_path
            if self.file_ext == '.dwg':
                # Konwertuj DWG na DXF używając ODA
                temp_dxf = tempfile.mktemp(suffix='.dxf')
                if convert_dwg_to_dxf(self.file_path, temp_dxf):
                    file_to_load = temp_dxf
                else:
                    self.show_error("Nie można przekonwertować pliku DWG.\nUpewnij się że ODA File Converter jest zainstalowany.\n\nPobierz z: https://www.opendesign.com/guestfiles/oda_file_converter")
                    return

            # Utwórz figure matplotlib
            fig = Figure(figsize=(12, 7), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            # Użyj preview_file_2d z mfgviewer
            from mfgviewer.dxf_preview import preview_file_2d
            preview_file_2d(Path(file_to_load), ax, show_bbox=True)

            # Osadź matplotlib w Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.viewer_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # Dodaj toolbar
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, self.viewer_frame)
            toolbar.update()

        except ImportError as e:
            # Fallback na Qt jeśli matplotlib nie zadziała
            self.load_2d_file_qt()
        except Exception as e:
            self.show_error(f"Błąd ładowania DXF/DWG:\n{str(e)}")

    def load_2d_file_qt(self):
        """Załaduj plik 2D używając Qt (fallback)"""
        if not HAS_QT:
            self.show_error("PySide6 nie jest zainstalowane.\nZainstaluj: pip install PySide6")
            return

        # Utwórz lub pobierz aplikację Qt
        self.qt_app = QApplication.instance()
        if self.qt_app is None:
            self.qt_app = QApplication([])

        # Utwórz widget DXF viewer
        try:
            self.qt_widget = DxfCanvas()
            self.qt_widget.set_background("black")

            # Osadź widget Qt w Tkinter
            # Na Windows możemy użyć winId
            window_id = self.viewer_frame.winfo_id()
            window = QWindow.fromWinId(window_id)
            container = QWidget.createWindowContainer(window)

            # Pokaż widget
            self.qt_widget.show()

            # Załaduj plik
            self.qt_widget.load_path(self.file_path)

            # Proces Qt events
            self.process_qt_events()

        except Exception as e:
            self.show_error(f"Błąd ładowania DXF/DWG (Qt):\n{str(e)}")

    def load_3d_file(self):
        """Załaduj plik 3D (STEP/STL)"""
        if not HAS_QT:
            self.show_error("PySide6 nie jest zainstalowane.\nZainstaluj: pip install PySide6")
            return

        if not HAS_VIEWERS:
            self.show_error("Moduły VTK nie są zainstalowane.\nZainstaluj: pip install vtk")
            return

        # Ukryj loading label
        self.loading_label.pack_forget()

        # Utwórz lub pobierz aplikację Qt
        self.qt_app = QApplication.instance()
        if self.qt_app is None:
            self.qt_app = QApplication([])

        # Utwórz widget VTK viewer
        try:
            from mfgviewer.backend_vtk import VtkViewerWidget

            # Utwórz kontener Qt
            container_widget = QWidget()
            layout = QVBoxLayout(container_widget)
            layout.setContentsMargins(0, 0, 0, 0)

            # Utwórz VTK widget
            self.qt_widget = VtkViewerWidget()
            layout.addWidget(self.qt_widget)

            # Embed Qt widget w Tkinter frame
            # Używamy prostszego podejścia - otwórz w nowym oknie Qt
            container_widget.setWindowTitle(f"Podgląd 3D: {Path(self.file_path).name}")
            container_widget.resize(900, 600)

            # Załaduj plik - konwertuj ścieżkę na string z forward slashes
            file_path_str = str(self.file_path).replace('\\', '/')
            self.qt_widget.load_path(file_path_str)

            # Pokaż okno
            container_widget.show()

            # Schowaj Tkinter loading frame
            self.viewer_frame.pack_forget()

            # Dodaj info
            info_label = ctk.CTkLabel(
                self,
                text="ℹ️ Podgląd 3D otwarty w osobnym oknie",
                font=ctk.CTkFont(size=12)
            )
            info_label.pack(expand=True)

            # Przechowaj referencję
            self.qt_container = container_widget

            # Proces Qt events
            self.process_qt_events()

        except Exception as e:
            self.show_error(f"Błąd ładowania 3D:\n{str(e)}\n{traceback.format_exc()}")

    def load_image_file(self):
        """Załaduj plik graficzny"""
        # Ukryj loading label
        self.loading_label.pack_forget()

        try:
            # Użyj PIL do załadowania obrazu
            img = Image.open(self.file_path)

            # Przeskaluj do rozmiaru okna zachowując proporcje
            display_size = (self.viewer_frame.winfo_width() - 20,
                          self.viewer_frame.winfo_height() - 20)
            img.thumbnail(display_size, Image.Resampling.LANCZOS)

            # Konwertuj na PhotoImage dla Tkinter
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)

            # Wyświetl w Label
            img_label = tk.Label(self.viewer_frame, image=photo, bg='black')
            img_label.image = photo  # Zachowaj referencję
            img_label.pack(expand=True)

        except Exception as e:
            self.show_error(f"Błąd ładowania obrazu:\n{str(e)}")

    def process_qt_events(self):
        """Przetwarzaj eventy Qt"""
        if self.qt_app:
            self.qt_app.processEvents()
            # Powtarzaj co 50ms dopóki okno jest otwarte
            if self.winfo_exists():
                self.after(50, self.process_qt_events)

    def show_error(self, message: str):
        """Pokaż komunikat o błędzie"""
        self.loading_label.configure(
            text=f"❌ {message}",
            fg_color="darkred"
        )
        self.loading_label.pack(expand=True)

    def close_viewer(self):
        """Zamknij viewer i wyczyść zasoby"""
        # Zatrzymaj przetwarzanie Qt events
        if self.qt_widget:
            try:
                self.qt_widget.close()
                self.qt_widget.deleteLater()
            except:
                pass

        # Zamknij Qt container jeśli istnieje
        if hasattr(self, 'qt_container'):
            try:
                self.qt_container.close()
            except:
                pass

        # Zamknij okno
        self.destroy()


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

        # Podgląd - zwiększony do 220x220 dla miniatur 200x200
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
            width=100,
            command=self.show_preview,
            state="disabled"
        )
        self.preview_button.pack(side="left", padx=2)

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

    def show_placeholder(self):
        """Pokaż placeholder w preview"""
        try:
            # Utwórz prosty placeholder 200x200
            placeholder_img = ThumbnailGenerator.create_placeholder((200, 200), self.title[:10])
            img = Image.open(io.BytesIO(placeholder_img))

            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo  # Zachowaj referencję
        except:
            self.preview_label.configure(text="Brak podglądu", image="")

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

            # Generuj i wyświetl miniaturę automatycznie
            self.generate_and_display_thumbnail()

            # Automatycznie wybierz to źródło
            self.radio_var.set(self.radio_value)

    def generate_and_display_thumbnail(self):
        """Generuj i wyświetl miniaturę"""
        if not self.file_path:
            return

        self.generate_thumbnail()

        # Wyświetl miniaturę jeśli została wygenerowana
        if self.thumbnail_data:
            try:
                img = Image.open(io.BytesIO(self.thumbnail_data))
                # Miniatura już jest 200x200, nie skaluj dodatkowo

                from PIL import ImageTk
                photo = ImageTk.PhotoImage(img)
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo  # Zachowaj referencję
            except Exception as e:
                print(f"Błąd wyświetlania miniatury: {e}")
                self.show_placeholder()

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

    def get_preview_4k(self) -> Optional[bytes]:
        """Zwróć dane podglądu 4K"""
        return self.preview_4k_data


def test_viewer():
    """Test viewera"""
    root = ctk.CTk()
    root.title("Test Integrated Viewer V2")
    root.geometry("900x500")

    # Radio variable
    source_var = tk.StringVar(value="")

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
    status = ctk.CTkLabel(root, text="Wybierz plik do podglądu")
    status.pack(pady=10)

    def update_status(*args):
        source = source_var.get()
        if source:
            status.configure(text=f"✓ Wybrane źródło: {source}")
        else:
            status.configure(text="Wybierz plik do podglądu")

    source_var.trace('w', update_status)

    root.mainloop()


if __name__ == "__main__":
    test_viewer()