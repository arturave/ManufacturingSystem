#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct FreeCAD test - checks if FreeCAD can read the file
"""

import os
import sys
import json
import subprocess
import tempfile

# Get FreeCAD path from environment
FREECAD_CMD = os.environ.get('FREECAD_CMD', r'C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe')

def test_freecad_direct(cad_file):
    """Test FreeCAD directly"""

    # Create a simple test script
    test_script = '''
import sys
import json

try:
    print("Starting FreeCAD test...")
    import FreeCAD as App
    import Part

    input_file = sys.argv[1]
    print(f"Loading file: {input_file}")

    # Create document
    doc = App.newDocument("TestDoc")

    # Try to import
    try:
        Part.insert(input_file, doc.Name)
        print("File imported successfully")
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)

    # Count objects
    print(f"Number of objects: {len(doc.Objects)}")

    # Get shapes
    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, 'Shape'):
            shapes.append(obj.Shape)
            print(f"Found shape: {obj.Name}")

    if shapes:
        compound = Part.makeCompound(shapes)
        bbox = compound.BoundBox

        print(f"Bounding box:")
        print(f"  X: {bbox.XMin:.2f} to {bbox.XMax:.2f} (width: {bbox.XLength:.2f})")
        print(f"  Y: {bbox.YMin:.2f} to {bbox.YMax:.2f} (height: {bbox.YLength:.2f})")
        print(f"  Z: {bbox.ZMin:.2f} to {bbox.ZMax:.2f} (depth: {bbox.ZLength:.2f})")
        print(f"  Volume: {compound.Volume:.2f} mm3")
        print(f"  Surface Area: {compound.Area:.2f} mm2")

        result = {
            'success': True,
            'width': bbox.XLength,
            'height': bbox.YLength,
            'depth': bbox.ZLength,
            'volume': compound.Volume,
            'area': compound.Area
        }
    else:
        print("No shapes found in the file")
        result = {'success': False, 'error': 'No shapes found'}

    # Save result
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as f:
            json.dump(result, f)

    print("Test completed")
    App.closeDocument(doc.Name)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''

    # Write script to temp file
    script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    script_file.write(test_script)
    script_file.close()

    # Output file
    output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    output_file.close()

    try:
        print(f"Testing with FreeCAD: {FREECAD_CMD}")
        print(f"Input file: {cad_file}")
        print("-" * 60)

        # Run FreeCAD
        cmd = [FREECAD_CMD, '-c', script_file.name, cad_file, output_file.name]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        print("FreeCAD Output:")
        print(result.stdout)

        if result.stderr:
            print("FreeCAD Errors:")
            print(result.stderr)

        # Check if output was created
        if os.path.exists(output_file.name) and os.path.getsize(output_file.name) > 0:
            with open(output_file.name, 'r') as f:
                data = json.load(f)
                print("\nExtracted Data:")
                print(json.dumps(data, indent=2))

                if data.get('success'):
                    print("\n[SUCCESS] Geometry extraction successful!")
                else:
                    print("\n[FAILED] Geometry extraction failed")
        else:
            print("\nNo output file created - FreeCAD may have failed")

    except subprocess.TimeoutExpired:
        print("FreeCAD timed out - the file may be too complex")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(script_file.name)
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)
        except:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_freecad_direct(sys.argv[1])
    else:
        print("Usage: python test_freecad_direct.py <cad_file>")
        print("Example: python test_freecad_direct.py c:/temp/test.stp")