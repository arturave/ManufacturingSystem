#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for DXF rendering with PyMuPDF backend
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.append('.')

# Import the CAD processing module
from cad_processing import CADProcessor, EZDXF_AVAILABLE, PYMUPDF_AVAILABLE

def test_dxf_rendering():
    """Test DXF rendering capabilities with new ezdxf implementation"""
    print("=" * 60)
    print("DXF Rendering Test - Nowa implementacja z ezdxf")
    print("=" * 60)

    # Check module availability
    print(f"EZDXF available: {EZDXF_AVAILABLE}")
    print(f"PyMuPDF available: {PYMUPDF_AVAILABLE}")
    print()

    if not EZDXF_AVAILABLE:
        print("ERROR: ezdxf is not available. Install with: pip install ezdxf")
        return False

    # Test DXF file path (user needs to provide)
    test_file = input("Podaj sciezke do pliku DXF/DWG do testowania (lub Enter dla pliku testowego): ").strip()

    if not test_file:
        print("\nGenerowanie testowego pliku DXF...")
        test_file = test_create_simple_dxf()
        if not test_file:
            print("Nie można utworzyć testowego pliku DXF")
            return False

    if not os.path.exists(test_file):
        print(f"Plik nie istnieje: {test_file}")
        return False

    # Create temp output files for both resolutions
    temp_high_res = tempfile.NamedTemporaryFile(suffix='_high.png', delete=False)
    high_res_path = temp_high_res.name
    temp_high_res.close()

    temp_low_res = tempfile.NamedTemporaryFile(suffix='_low.png', delete=False)
    low_res_path = temp_low_res.name
    temp_low_res.close()

    print(f"\nPrzetwarzanie pliku: {test_file}")
    print(f"Plik hi-res: {high_res_path}")
    print(f"Plik low-res: {low_res_path}")
    print()

    # Process the file - test both resolutions
    try:
        print("Test 1: Generowanie obu rozdzielczości...")
        high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
            test_file,
            high_res_path,
            low_res_path
        )

        if high_success:
            # Check if high-res output file was created
            if os.path.exists(high_res_path):
                file_size = os.path.getsize(high_res_path)
                print(f"[OK] SUKCES - Hi-Res: Wygenerowano podgląd PNG (300 DPI)")
                print(f"   Rozmiar pliku: {file_size:,} bajtów")
                print(f"   Ścieżka: {high_res_path}")
            else:
                print("[ERROR] BŁĄD: Plik hi-res nie został utworzony")

        if low_success:
            # Check if low-res output file was created
            if os.path.exists(low_res_path):
                file_size = os.path.getsize(low_res_path)
                print(f"[OK] SUKCES - Low-Res: Wygenerowano miniaturę (72 DPI)")
                print(f"   Rozmiar pliku: {file_size:,} bajtów")
                print(f"   Ścieżka: {low_res_path}")
            else:
                print("[ERROR] BŁĄD: Plik low-res nie został utworzony")

        if high_success or low_success:
            # Open the image in default viewer (Windows)
            import subprocess
            try:
                if high_success:
                    subprocess.run(['start', '', high_res_path], shell=True)
                    print("\n   Otwieranie podglądu hi-res...")
                if low_success:
                    subprocess.run(['start', '', low_res_path], shell=True)
                    print("   Otwieranie podglądu low-res...")
            except:
                print(f"\n   Nie można automatycznie otworzyć plików.")
                print(f"   Sprawdź ręcznie:")
                if high_success:
                    print(f"   - Hi-res: {high_res_path}")
                if low_success:
                    print(f"   - Low-res: {low_res_path}")
        else:
            print("[ERROR] BŁĄD: Przetwarzanie nie powiodło się")

        success = high_success or low_success

    except Exception as e:
        print(f"[ERROR] BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        success = False

    print("\n" + "=" * 60)
    return success

def test_create_simple_dxf():
    """Create a simple test DXF file"""
    if not EZDXF_AVAILABLE:
        print("Cannot create test DXF - ezdxf not available")
        return None

    import ezdxf

    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Add some simple geometry
    # Rectangle
    points = [(0, 0), (100, 0), (100, 50), (0, 50), (0, 0)]
    msp.add_lwpolyline(points)

    # Circle
    msp.add_circle(center=(50, 25), radius=15)

    # Text
    msp.add_text('TEST DXF', dxfattribs={'height': 5, 'insert': (40, 60)})

    # Line
    msp.add_line((10, 10), (90, 40))

    # Save
    test_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
    test_path = test_file.name
    test_file.close()

    doc.saveas(test_path)
    print(f"Created test DXF file: {test_path}")

    return test_path

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Test renderowania DXF/DWG - Nowa implementacja ezdxf")
    print("=" * 60)
    print("\nTa wersja używa nowego workflow z dokumentacji ezdxf:")
    print("- PyMuPDF backend dla wysokiej jakości")
    print("- Automatyczne wykrywanie rozmiaru rysunku")
    print("- Generowanie dwóch rozdzielczości (hi-res i low-res)")
    print("- Fallback do matplotlib jeśli PyMuPDF nie działa")
    print("\n" + "=" * 60 + "\n")

    test_dxf_rendering()