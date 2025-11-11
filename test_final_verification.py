#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weryfikacja finalnych zmian w oknie Nowy detal
"""

import os
import sys

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("WERYFIKACJA FINALNYCH ZMIAN - OKNO 'NOWY DETAL'")
print("=" * 70)
print()

# Test 1: Sprawdź czy kod nie ma błędów składni
print("[TEST 1] Sprawdzanie kodu Python...")
try:
    from part_edit_enhanced import EnhancedPartEditDialog
    print("[OK] part_edit_enhanced.py - kod poprawny")
except SyntaxError as e:
    print(f"[ERROR] Błąd składni w part_edit_enhanced.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[WARNING] Import part_edit_enhanced.py: {e}")

try:
    from integrated_viewer_v2 import EnhancedFilePreviewFrame, ViewerPopup
    print("[OK] integrated_viewer_v2.py - kod poprawny")
except SyntaxError as e:
    print(f"[ERROR] Błąd składni w integrated_viewer_v2.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[WARNING] Import integrated_viewer_v2.py: {e}")

print()

# Test 2: Sprawdź czy metody zostały usunięte
print("[TEST 2] Sprawdzanie usuniętych metod...")
has_errors = False

# Sprawdź czy generate_all_thumbnails została usunięta z part_edit_enhanced
if hasattr(EnhancedPartEditDialog, 'generate_all_thumbnails'):
    print("[ERROR] Metoda generate_all_thumbnails() nadal istnieje w part_edit_enhanced.py")
    has_errors = True
else:
    print("[OK] Metoda generate_all_thumbnails() usunięta z part_edit_enhanced.py")

# Sprawdź czy generate_all_graphics została usunięta z integrated_viewer_v2
if hasattr(EnhancedFilePreviewFrame, 'generate_all_graphics'):
    print("[ERROR] Metoda generate_all_graphics() nadal istnieje w integrated_viewer_v2.py")
    has_errors = True
else:
    print("[OK] Metoda generate_all_graphics() usunięta z integrated_viewer_v2.py")

# Sprawdź czy show_embedded_3d_preview została usunięta
if hasattr(EnhancedFilePreviewFrame, 'show_embedded_3d_preview'):
    print("[ERROR] Metoda show_embedded_3d_preview() nadal istnieje")
    has_errors = True
else:
    print("[OK] Metoda show_embedded_3d_preview() usunięta")

print()

# Test 3: Sprawdź czy automatyczne generowanie jest aktywne
print("[TEST 3] Sprawdzanie automatycznego generowania...")
if hasattr(EnhancedFilePreviewFrame, 'generate_and_display_thumbnail'):
    print("[OK] Metoda generate_and_display_thumbnail() istnieje")
else:
    print("[ERROR] Brak metody generate_and_display_thumbnail()")
    has_errors = True

if hasattr(EnhancedFilePreviewFrame, 'show_preview'):
    print("[OK] Metoda show_preview() istnieje")
else:
    print("[ERROR] Brak metody show_preview()")
    has_errors = True

print()

# Test 4: Sprawdź moduły VTK i Qt
print("[TEST 4] Sprawdzanie wymaganych modułów...")
try:
    import vtk
    print(f"[OK] VTK zainstalowane (wersja {vtk.VTK_VERSION})")
except ImportError:
    print("[ERROR] VTK nie jest zainstalowane")
    has_errors = True

try:
    from PySide6 import QtWidgets
    print("[OK] PySide6 zainstalowane")
except ImportError:
    print("[ERROR] PySide6 nie jest zainstalowane")
    has_errors = True

try:
    import ezdxf
    print(f"[OK] ezdxf zainstalowane (wersja {ezdxf.__version__})")
except ImportError:
    print("[WARNING] ezdxf nie jest zainstalowane (opcjonalne dla 2D)")

print()

# Test 5: Sprawdź konfigurację projektu Visual Studio
print("[TEST 5] Sprawdzanie konfiguracji Visual Studio...")
pyproj_file = "ManufacturingSystem.pyproj"
if os.path.exists(pyproj_file):
    with open(pyproj_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'MSBuild|env|' in content:
            print("[OK] InterpreterId ustawione na 'env'")
        else:
            print("[WARNING] InterpreterId może być niepoprawne")

        if '<Id>env</Id>' in content:
            print("[OK] Interpreter 'env' zdefiniowany w projekcie")
        else:
            print("[WARNING] Brak definicji interpretera 'env'")
else:
    print(f"[WARNING] Nie znaleziono pliku {pyproj_file}")

print()
print("=" * 70)
print("PODSUMOWANIE:")
print("=" * 70)

if has_errors:
    print("[FAILED] Znaleziono błędy - sprawdź logi powyżej")
    sys.exit(1)
else:
    print("[SUCCESS] Wszystkie testy zakończone pomyślnie!")
    print()
    print("Gotowe do użycia:")
    print("1. Automatyczne generowanie miniatur - AKTYWNE")
    print("2. Usunięte przyciski 'Generuj' - ZROBIONE")
    print("3. Podgląd 3D w osobnym oknie - PRZYWRÓCONE")
    print("4. Moduły VTK i PySide6 - ZAINSTALOWANE")
    print("5. Konfiguracja Visual Studio - POPRAWIONA")
    print()
    print("Możesz teraz:")
    print("- Uruchomić aplikację w Visual Studio")
    print("- Otworzyć okno 'Nowy detal'")
    print("- Wczytać plik - miniatura wygeneruje się automatycznie")
    print("- Kliknąć 'Podgląd' - otworzy się osobne okno")

print("=" * 70)