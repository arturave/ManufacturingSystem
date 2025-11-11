#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated test for CAD processing - no user interaction required
"""

import os
import sys
import tempfile
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.append('.')

# Import the CAD processing module
from cad_processing import CADProcessor, EZDXF_AVAILABLE, PYMUPDF_AVAILABLE

def create_test_dxf():
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
    msp.add_text('TEST DXF - ManufacturingSystem', dxfattribs={'height': 5, 'insert': (10, 60)})

    # Lines
    msp.add_line((10, 10), (90, 10))
    msp.add_line((10, 40), (90, 40))

    # Arc
    msp.add_arc(center=(25, 25), radius=8, start_angle=0, end_angle=180)

    # Save
    test_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
    test_path = test_file.name
    test_file.close()

    doc.saveas(test_path)
    return test_path

def run_automated_test():
    """Run automated CAD processing test"""
    print("=" * 70)
    print("AUTOMATED CAD PROCESSING TEST")
    print("=" * 70)
    print()

    # Check module availability
    print("Sprawdzanie dostępności modułów:")
    print(f"  ✓ EZDXF: {EZDXF_AVAILABLE}")
    print(f"  ✓ PyMuPDF: {PYMUPDF_AVAILABLE}")
    print()

    if not EZDXF_AVAILABLE:
        print("ERROR: ezdxf is not available. Install with: pip install ezdxf")
        return False

    # Create test DXF file
    print("Krok 1: Tworzenie testowego pliku DXF...")
    test_dxf = create_test_dxf()
    if not test_dxf:
        print("  ✗ BŁĄD: Nie można utworzyć testowego pliku DXF")
        return False
    print(f"  ✓ Utworzono: {test_dxf}")
    print()

    # Create output paths
    temp_high_res = tempfile.NamedTemporaryFile(suffix='_high_res.png', delete=False)
    high_res_path = temp_high_res.name
    temp_high_res.close()

    temp_low_res = tempfile.NamedTemporaryFile(suffix='_low_res.png', delete=False)
    low_res_path = temp_low_res.name
    temp_low_res.close()

    print("Krok 2: Przetwarzanie DXF do PNG (obie rozdzielczości)...")
    print(f"  Hi-Res output: {high_res_path}")
    print(f"  Low-Res output: {low_res_path}")
    print()

    # Process the file
    try:
        high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
            test_dxf,
            high_res_path,
            low_res_path
        )

        print("Krok 3: Weryfikacja wyników...")
        print()

        # Check high-res
        if high_success and os.path.exists(high_res_path):
            file_size = os.path.getsize(high_res_path)
            print(f"  ✓ Hi-Res PNG (300 DPI): SUKCES")
            print(f"    Rozmiar: {file_size:,} bajtów ({file_size/1024:.1f} KB)")
            print(f"    Ścieżka: {high_res_path}")
        else:
            print(f"  ✗ Hi-Res PNG: BŁĄD")

        print()

        # Check low-res
        if low_success and os.path.exists(low_res_path):
            file_size = os.path.getsize(low_res_path)
            print(f"  ✓ Low-Res PNG (72 DPI): SUKCES")
            print(f"    Rozmiar: {file_size:,} bajtów ({file_size/1024:.1f} KB)")
            print(f"    Ścieżka: {low_res_path}")
        else:
            print(f"  ✗ Low-Res PNG: BŁĄD")

        print()

        # Open files if successful
        if high_success or low_success:
            import subprocess
            try:
                if high_success:
                    subprocess.run(['start', '', high_res_path], shell=True)
                    print(f"  → Otwieranie hi-res w przeglądarce...")
                if low_success:
                    subprocess.run(['start', '', low_res_path], shell=True)
                    print(f"  → Otwieranie low-res w przeglądarce...")
            except Exception as e:
                print(f"  ! Nie można automatycznie otworzyć plików: {e}")

        print()
        print("=" * 70)

        if high_success and low_success:
            print("WYNIK: ✓ TEST ZAKOŃCZONY SUKCESEM - WSZYSTKIE ROZDZIELCZOŚCI")
        elif high_success or low_success:
            print("WYNIK: ⚠ TEST CZĘŚCIOWO UDANY - JEDNA ROZDZIELCZOŚĆ")
        else:
            print("WYNIK: ✗ TEST NIEUDANY")

        print("=" * 70)

        return high_success and low_success

    except Exception as e:
        print(f"✗ BŁĄD podczas przetwarzania: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 70)
        print("WYNIK: ✗ TEST NIEUDANY - WYSTĄPIŁ WYJĄTEK")
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = run_automated_test()
    sys.exit(0 if success else 1)
