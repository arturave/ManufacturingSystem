#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for FreeCAD-based CAD rendering
Tests the new FreeCAD integration for STEP/IGES file processing
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_freecad_renderer():
    """Test FreeCAD renderer module"""
    print("=" * 60)
    print("Testing FreeCAD Renderer")
    print("=" * 60)

    try:
        from freecad_renderer import FreeCADRenderer

        # Try to create renderer
        print("\n1. Checking FreeCAD installation...")
        try:
            renderer = FreeCADRenderer()
            print(f"   ✓ FreeCAD found at: {renderer.freecad_cmd}")
        except Exception as e:
            print(f"   ✗ FreeCAD not found: {e}")
            print("\nPlease install FreeCAD from: https://www.freecad.org/downloads.php")
            print("Or update FREECAD_CMD in .env file with the correct path")
            return False

        # Test with a sample file if provided
        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            if os.path.exists(test_file):
                print(f"\n2. Testing rendering with: {test_file}")
                output_file = "test_freecad_output.png"

                try:
                    success = renderer.render_with_info_fallback(
                        test_file,
                        output_file,
                        width=1920,
                        height=1080
                    )

                    if success and os.path.exists(output_file):
                        file_size = os.path.getsize(output_file) / 1024  # KB
                        print(f"   ✓ Rendering successful!")
                        print(f"   ✓ Output: {output_file} ({file_size:.1f} KB)")

                        # Try to extract geometry info
                        print("\n3. Extracting geometry information...")
                        info = renderer.extract_geometry_info(test_file)
                        if info:
                            print("   ✓ Geometry extraction successful!")
                            bbox = info.get('bounding_box', {})
                            print(f"   Dimensions: {bbox.get('width', 0):.1f} x {bbox.get('height', 0):.1f} x {bbox.get('depth', 0):.1f} mm")
                            print(f"   Volume: {info.get('volume', 0):.1f} mm³")
                            print(f"   Surface Area: {info.get('area', 0):.1f} mm²")
                    else:
                        print(f"   ✗ Rendering failed or output not created")

                except Exception as e:
                    print(f"   ✗ Error during rendering: {e}")
                    import traceback
                    traceback.print_exc()

            else:
                print(f"   ✗ Test file not found: {test_file}")
        else:
            print("\n2. No test file provided")
            print("   Usage: python test_freecad_rendering.py <path_to_step_or_iges_file>")
            print("\n   To test rendering, provide a STEP or IGES file")

        return True

    except ImportError as e:
        print(f"✗ Could not import freecad_renderer: {e}")
        return False


def test_cad_processor_integration():
    """Test integration with CADProcessor"""
    print("\n" + "=" * 60)
    print("Testing CADProcessor Integration")
    print("=" * 60)

    try:
        from cad_processing import CADProcessor

        print("\n1. Checking CADProcessor with FreeCAD support...")

        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            if os.path.exists(test_file):
                print(f"   Testing with: {test_file}")

                # Test high/low resolution generation
                high_res = "test_cad_high.png"
                low_res = "test_cad_low.png"

                high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
                    test_file,
                    high_res,
                    low_res
                )

                if high_success:
                    print(f"   ✓ High-res image created: {high_res}")
                else:
                    print(f"   ✗ High-res image creation failed")

                if low_success:
                    print(f"   ✓ Low-res thumbnail created: {low_res}")
                else:
                    print(f"   ✗ Low-res thumbnail creation failed")

                return high_success or low_success
        else:
            print("   Skipping - no test file provided")

        return True

    except Exception as e:
        print(f"✗ Error testing CADProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check all required dependencies"""
    print("=" * 60)
    print("Checking Dependencies")
    print("=" * 60)

    dependencies = {
        'PIL': 'pillow',
        'dotenv': 'python-dotenv',
        'ezdxf': 'ezdxf',
        'matplotlib': 'matplotlib',
    }

    all_available = True

    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module} ({package}) - installed")
        except ImportError:
            print(f"✗ {module} ({package}) - NOT installed")
            print(f"  Install with: pip install {package}")
            all_available = False

    # Check FreeCAD separately
    print("\nChecking FreeCAD:")
    try:
        from freecad_renderer import FreeCADRenderer
        renderer = FreeCADRenderer()
        print(f"✓ FreeCAD - found at {renderer.freecad_cmd}")
    except:
        print("✗ FreeCAD - NOT found")
        print("  Download from: https://www.freecad.org/downloads.php")
        all_available = False

    return all_available


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print(" FreeCAD CAD Rendering Test Suite")
    print("=" * 60)

    # Check dependencies
    deps_ok = check_dependencies()

    if not deps_ok:
        print("\n⚠ Some dependencies are missing. Install them to enable full functionality.")

    # Test FreeCAD renderer
    print("")
    freecad_ok = test_freecad_renderer()

    # Test CADProcessor integration
    processor_ok = test_cad_processor_integration()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Dependencies: {'✓ OK' if deps_ok else '✗ Missing'}")
    print(f"FreeCAD Renderer: {'✓ OK' if freecad_ok else '✗ Failed'}")
    print(f"CADProcessor Integration: {'✓ OK' if processor_ok else '✗ Failed'}")

    if freecad_ok and processor_ok:
        print("\n✓ All tests passed! FreeCAD rendering is ready to use.")
    else:
        print("\n⚠ Some tests failed. Please check the output above for details.")


if __name__ == "__main__":
    main()