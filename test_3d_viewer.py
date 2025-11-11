#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test sprawdzający działanie podglądu 3D z VTK
"""

import os
import sys
import tempfile

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("TEST PODGLĄDU 3D")
print("=" * 60)
print()

# Sprawdź dostępność modułów
try:
    from PySide6 import QtWidgets, QtCore
    print("[OK] PySide6 zainstalowane")
except ImportError as e:
    print(f"[ERROR] Brak PySide6: {e}")
    sys.exit(1)

try:
    import vtk
    print(f"[OK] VTK zainstalowane (wersja {vtk.VTK_VERSION})")
except ImportError as e:
    print(f"[ERROR] Brak VTK: {e}")
    sys.exit(1)

try:
    import ezdxf
    print(f"[OK] ezdxf zainstalowane (wersja {ezdxf.__version__})")
except ImportError as e:
    print(f"[ERROR] Brak ezdxf: {e}")

try:
    import matplotlib
    print(f"[OK] matplotlib zainstalowane (wersja {matplotlib.__version__})")
except ImportError as e:
    print(f"[ERROR] Brak matplotlib: {e}")

# Sprawdź mfgviewer
print()
print("Sprawdzanie modułu mfgviewer...")
mfgviewer_path = os.path.join(os.path.dirname(__file__), 'mfgviewer')
if os.path.exists(mfgviewer_path):
    print(f"[OK] Folder mfgviewer istnieje: {mfgviewer_path}")
    sys.path.insert(0, mfgviewer_path)

    try:
        from mfgviewer.dxf_preview import DxfCanvas, preview_file_2d, SUPPORTED_2D
        print("[OK] Moduł dxf_preview załadowany")
        print(f"    Obsługiwane formaty 2D: {SUPPORTED_2D}")
    except ImportError as e:
        print(f"[WARNING] Nie można załadować dxf_preview: {e}")

    try:
        from mfgviewer.backend_vtk import VtkViewerWidget, SUPPORTED_3D
        print("[OK] Moduł backend_vtk załadowany")
        print(f"    Obsługiwane formaty 3D: {SUPPORTED_3D}")
    except ImportError as e:
        print(f"[WARNING] Nie można załadować backend_vtk: {e}")
else:
    print(f"[ERROR] Brak folderu mfgviewer w: {mfgviewer_path}")

# Test integracji z integrated_viewer_v2
print()
print("Sprawdzanie integracji...")
try:
    from integrated_viewer_v2 import (
        EnhancedFilePreviewFrame,
        ThumbnailGenerator,
        ViewerPopup
    )
    print("[OK] Moduły integrated_viewer_v2 załadowane")
except ImportError as e:
    print(f"[ERROR] Nie można załadować integrated_viewer_v2: {e}")

# Utwórz przykładowy plik STL do testów
print()
print("Tworzenie testowego pliku STL...")
try:
    test_stl = os.path.join(tempfile.gettempdir(), "test_cube.stl")

    # Prosty sześcian w formacie STL ASCII
    stl_content = """solid cube
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 1 1 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 1 0
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 1 1
      vertex 1 0 1
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 0 1 1
      vertex 1 1 1
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 0 0 0
      vertex 1 0 1
      vertex 1 0 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 1 0 1
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 0 1 0
      vertex 1 1 0
      vertex 1 1 1
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 0 1 0
      vertex 1 1 1
      vertex 0 1 1
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 0 1 1
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 1
      vertex 0 0 1
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 1 0 0
      vertex 1 1 1
      vertex 1 1 0
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 1 0 0
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
endsolid cube"""

    with open(test_stl, 'w') as f:
        f.write(stl_content)

    print(f"[OK] Utworzono testowy plik STL: {test_stl}")

    # Test wczytywania STL przez VTK
    print()
    print("Test wczytywania pliku STL przez VTK...")
    try:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(test_stl)
        reader.Update()

        polydata = reader.GetOutput()
        n_points = polydata.GetNumberOfPoints()
        n_cells = polydata.GetNumberOfCells()

        print(f"[OK] Plik STL wczytany poprawnie")
        print(f"    Liczba punktów: {n_points}")
        print(f"    Liczba powierzchni: {n_cells}")
    except Exception as e:
        print(f"[ERROR] Błąd wczytywania STL: {e}")

except Exception as e:
    print(f"[ERROR] Nie można utworzyć testowego pliku STL: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("PODSUMOWANIE:")
print()
print("Jeśli wszystkie komponenty są zainstalowane poprawnie,")
print("podgląd 3D powinien działać w oknie 'Nowy detal'.")
print()
print("Możesz teraz:")
print("1. Uruchomić ponownie test_part_edit_changes.py")
print("2. Wczytać plik 3D (STEP, STL, IGES)")
print("3. Kliknąć 'Podgląd' - powinien otworzyć się osadzony widok 3D")
print("=" * 60)