#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for 3D CAD file rendering
Tests STEP and IGES file processing with the updated render3d module
"""

import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

# Import modules
from cad_processing import CADProcessor

# Check if render3d is available
try:
    from render3d import (
        StepIgesRenderer,
        OCC_AVAILABLE as RENDER3D_AVAILABLE,
        SUPABASE_AVAILABLE,
        generate_local_only,
        generate_and_upload,
        auto_thumbnail_on_part_create
    )
    RENDER3D_MODULE = True
except ImportError:
    RENDER3D_MODULE = False
    RENDER3D_AVAILABLE = False
    SUPABASE_AVAILABLE = False
    print("Warning: render3d module not found")


def create_test_step_file():
    """Create a simple test STEP file (actually just returns None as we need real files)"""
    print("Note: STEP/IGES files must be actual 3D models.")
    print("      Cannot generate test files programmatically.")
    return None


def test_3d_rendering():
    """Test 3D file rendering capabilities"""
    print("=" * 70)
    print("TEST RENDEROWANIA PLIKÓW 3D (STEP/IGES)")
    print("=" * 70)
    print()

    # Check module availability
    print("Sprawdzanie dostępności modułów:")
    print(f"  • render3d module: {RENDER3D_MODULE}")
    if RENDER3D_MODULE:
        print(f"  • pythonocc-core (OCC): {RENDER3D_AVAILABLE}")
        print(f"  • supabase: {SUPABASE_AVAILABLE}")
    print()

    if not RENDER3D_MODULE:
        print("ERROR: render3d module is not available.")
        print("Make sure render3d.py is in the same directory.")
        return False

    if not RENDER3D_AVAILABLE:
        print("ERROR: pythonocc-core is not installed!")
        print()
        print("Aby zainstalować pythonocc-core:")
        print("1. Zainstaluj Anaconda lub Miniconda")
        print("2. Uruchom: conda install -c conda-forge pythonocc-core")
        print()
        print("Alternatywnie (tylko Windows):")
        print("  conda install -c dlr-sc pythonocc-core")
        print()
        return False

    # Test file path
    test_file = input("Podaj ścieżkę do pliku STEP/IGES do testowania (lub Enter aby pominąć): ").strip()

    if not test_file:
        print("\nBrak pliku testowego.")
        print("\nPrzykładowe pliki do testowania:")
        print("  • Pobierz przykładowe pliki STEP z: https://www.cad-resources.com/")
        print("  • Lub użyj własnych plików .stp, .step, .igs, .iges")
        return False

    if not os.path.exists(test_file):
        print(f"\nPlik nie istnieje: {test_file}")
        return False

    # Check file extension
    ext = Path(test_file).suffix.lower()
    if ext not in ['.stp', '.step', '.igs', '.iges']:
        print(f"\nNieobsługiwany format: {ext}")
        print("Obsługiwane formaty: .stp, .step, .igs, .iges")
        return False

    print(f"\nPrzetwarzanie pliku: {test_file}")
    print(f"Format: {ext.upper()}")
    print()

    # Test 1: Direct render3d module test
    print("TEST 1: Bezpośrednie renderowanie przez moduł render3d...")
    print("-" * 50)

    try:
        result = generate_local_only(
            test_file,
            render_size=(1200, 900),
            thumb_size=(300, 225)
        )

        print("[✓] SUKCES - Renderowanie zakończone")
        print(f"    Pełny obraz: {result['full_png_local']}")
        print(f"    Miniatura: {result['thumb_png_local']}")

        if result.get('bounding_box'):
            bbox = result['bounding_box']
            print(f"\n    Wymiary modelu:")
            print(f"      Szerokość: {bbox['width']:.2f} mm")
            print(f"      Wysokość: {bbox['height']:.2f} mm")
            print(f"      Głębokość: {bbox['depth']:.2f} mm")

        # Open the generated image
        import subprocess
        try:
            if sys.platform == 'win32':
                subprocess.run(['start', '', result['full_png_local']], shell=True)
                print("\n    → Otwieranie podglądu...")
        except:
            pass

        test1_success = True

    except Exception as e:
        print(f"[✗] BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        test1_success = False

    print()

    # Test 2: CADProcessor integration test
    print("TEST 2: Renderowanie przez CADProcessor (integracja)...")
    print("-" * 50)

    temp_high = tempfile.NamedTemporaryFile(suffix='_high.png', delete=False)
    high_res_path = temp_high.name
    temp_high.close()

    temp_low = tempfile.NamedTemporaryFile(suffix='_low.png', delete=False)
    low_res_path = temp_low.name
    temp_low.close()

    try:
        high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
            test_file,
            high_res_path,
            low_res_path
        )

        if high_success:
            file_size = os.path.getsize(high_res_path)
            print(f"[✓] Hi-Res PNG: SUKCES")
            print(f"    Rozmiar: {file_size:,} bajtów ({file_size/1024:.1f} KB)")
            print(f"    Ścieżka: {high_res_path}")
        else:
            print("[✗] Hi-Res PNG: BŁĄD")

        if low_success:
            file_size = os.path.getsize(low_res_path)
            print(f"[✓] Low-Res PNG: SUKCES")
            print(f"    Rozmiar: {file_size:,} bajtów ({file_size/1024:.1f} KB)")
            print(f"    Ścieżka: {low_res_path}")
        else:
            print("[✗] Low-Res PNG: BŁĄD")

        if high_success:
            # Open high-res image
            import subprocess
            try:
                if sys.platform == 'win32':
                    subprocess.run(['start', '', high_res_path], shell=True)
                    print("\n    → Otwieranie podglądu hi-res...")
            except:
                pass

        test2_success = high_success and low_success

    except Exception as e:
        print(f"[✗] BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        test2_success = False

    print()
    print("=" * 70)

    # Summary
    if test1_success and test2_success:
        print("WYNIK: ✓ WSZYSTKIE TESTY ZAKOŃCZONE SUKCESEM")
        print("\nSystem jest gotowy do renderowania plików 3D!")
    elif test1_success or test2_success:
        print("WYNIK: ⚠ CZĘŚCIOWY SUKCES")
        if test1_success:
            print("  ✓ Moduł render3d działa poprawnie")
        if test2_success:
            print("  ✓ Integracja z CADProcessor działa")
    else:
        print("WYNIK: ✗ TESTY NIEUDANE")
        print("\nSprawdź instalację pythonocc-core:")
        print("  conda install -c conda-forge pythonocc-core")

    print("=" * 70)

    return test1_success and test2_success


def test_3d_fallback():
    """Test fallback mechanism when pythonocc-core is not available"""
    print("=" * 70)
    print("TEST MECHANIZMU FALLBACK (gdy brak pythonocc-core)")
    print("=" * 70)
    print()

    test_file = "example.stp"  # Dummy file for testing

    # Create dummy test file
    with open(test_file, 'w') as f:
        f.write("ISO-10303-21;\n")
        f.write("HEADER;\n")
        f.write("FILE_DESCRIPTION(('Test STEP File'),'2;1');\n")
        f.write("FILE_NAME('test.stp','2024-01-01T00:00:00',(),(),'','','');\n")
        f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\n")
        f.write("ENDSEC;\n")
        f.write("DATA;\n")
        f.write("ENDSEC;\n")
        f.write("END-ISO-10303-21;\n")

    temp_output = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    output_path = temp_output.name
    temp_output.close()

    try:
        # Test CADProcessor with dummy STEP file
        success = CADProcessor.process_step_to_image(test_file, output_path)

        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[✓] Placeholder utworzony pomyślnie")
            print(f"    Rozmiar: {file_size:,} bajtów")
            print(f"    Ścieżka: {output_path}")

            # Try to open
            import subprocess
            try:
                if sys.platform == 'win32':
                    subprocess.run(['start', '', output_path], shell=True)
                    print("\n    → Otwieranie placeholder'a...")
            except:
                pass
        else:
            print("[✗] Nie udało się utworzyć placeholder'a")

    except Exception as e:
        print(f"[✗] BŁĄD: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)

    print()
    print("=" * 70)


def test_supabase_upload():
    """Test Supabase upload functionality"""
    print("=" * 70)
    print("TEST UPLOADU DO SUPABASE")
    print("=" * 70)
    print()

    if not RENDER3D_MODULE:
        print("ERROR: render3d module not available")
        return False

    if not SUPABASE_AVAILABLE:
        print("ERROR: Supabase not installed")
        print("Install with: pip install supabase")
        return False

    # Check environment variables
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Supabase credentials not configured")
        print("Add SUPABASE_URL and SUPABASE_KEY to your .env file")
        return False

    print("✓ Supabase configured")
    print(f"  URL: {SUPABASE_URL[:30]}...")
    print()

    # Get test file
    test_file = input("Podaj ścieżkę do pliku STEP/IGES do testowania uploadu: ").strip()

    if not test_file or not os.path.exists(test_file):
        print("Brak pliku testowego")
        return False

    print(f"\nPrzetwarzanie i upload: {test_file}")
    print()

    try:
        # Test generate_and_upload
        result = generate_and_upload(
            model_path=test_file,
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            part_id="TEST-123",
            order_process_no="2025-00001",
            render_size=(1200, 900),
            thumb_size=(360, 270)
        )

        print("[✓] SUKCES - Upload zakończony")
        print(f"    Lokalny pełny: {result['full_png_local']}")
        print(f"    Lokalny miniatura: {result['thumb_png_local']}")
        print(f"    Storage pełny: {result['full_png_storage_path']}")
        print(f"    Storage miniatura: {result['thumb_png_storage_path']}")
        print(f"    URL pełny: {result['full_png_url']}")
        print(f"    URL miniatura: {result['thumb_png_url']}")

        if result.get('bounding_box'):
            bbox = result['bounding_box']
            print(f"\n    Wymiary modelu:")
            print(f"      Szerokość: {bbox['width']:.2f} mm")
            print(f"      Wysokość: {bbox['height']:.2f} mm")
            print(f"      Głębokość: {bbox['depth']:.2f} mm")

        return True

    except Exception as e:
        print(f"[✗] BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hook_integration():
    """Test hook integration for auto thumbnail creation"""
    print("=" * 70)
    print("TEST INTEGRACJI HOOK")
    print("=" * 70)
    print()

    if not RENDER3D_MODULE:
        print("ERROR: render3d module not available")
        return False

    # Mock callbacks
    def on_success_update_db(meta: dict):
        print("✓ Hook callback - zapisywanie do DB:")
        print(f"  - thumb_url: {meta.get('thumb_png_url', 'N/A')}")
        print(f"  - full_url: {meta.get('full_png_url', 'N/A')}")

    def on_error_log(msg: str):
        print(f"✗ Hook error: {msg}")

    test_file = input("Podaj ścieżkę do pliku STEP/IGES (lub Enter aby pominąć): ").strip()

    if not test_file:
        print("Test pominięty")
        return False

    # Check environment
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("WARNING: Brak konfiguracji Supabase, test będzie ograniczony")

    print(f"\nTestowanie hooka dla: {test_file}")

    try:
        result = auto_thumbnail_on_part_create(
            model_path=test_file,
            part_id="HOOK-TEST-456",
            supabase_url=SUPABASE_URL or "https://dummy.supabase.co",
            supabase_key=SUPABASE_KEY or "dummy-key",
            order_process_no="2025-00042",
            on_success_update_db=on_success_update_db,
            on_error_log=on_error_log
        )

        if result:
            print("\n[✓] Hook wykonany pomyślnie")
        else:
            print("\n[✗] Hook nie zwrócił rezultatu")

        return result is not None

    except Exception as e:
        print(f"[✗] BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTER RENDEROWANIA PLIKÓW 3D")
    print("ManufacturingSystem - CAD 3D Support")
    print("=" * 70)

    print("\nWybierz test:")
    print("1. Test pełnego renderowania 3D (wymaga pythonocc-core)")
    print("2. Test mechanizmu fallback (placeholder)")
    print("3. Test uploadu do Supabase")
    print("4. Test integracji hook")
    print("5. Wszystkie testy")

    choice = input("\nWybór (1-5): ").strip()

    if choice == "1":
        test_3d_rendering()
    elif choice == "2":
        test_3d_fallback()
    elif choice == "3":
        test_supabase_upload()
    elif choice == "4":
        test_hook_integration()
    elif choice == "5":
        test_3d_rendering()
        print("\n")
        test_3d_fallback()
        print("\n")
        if SUPABASE_AVAILABLE:
            test_supabase_upload()
            print("\n")
            test_hook_integration()
    else:
        print("Nieprawidłowy wybór")

    print("\n")