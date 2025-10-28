#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeCAD-based 3D CAD File Renderer
Renders STEP/IGES files to PNG using FreeCAD in headless mode
Alternative to OpenCASCADE-based rendering
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
import base64

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class FreeCADRenderer:
    """Renders STEP/IGES files using FreeCAD"""

    def __init__(self, freecad_cmd_path: Optional[str] = None):
        """
        Initialize FreeCAD renderer

        Args:
            freecad_cmd_path: Path to FreeCADCmd.exe (if None, tries to find automatically)
        """
        self.freecad_cmd = freecad_cmd_path or self._find_freecad_cmd()
        if not self.freecad_cmd:
            raise RuntimeError("FreeCADCmd.exe not found. Please install FreeCAD or provide path.")

        if not os.path.exists(self.freecad_cmd):
            raise RuntimeError(f"FreeCADCmd.exe not found at: {self.freecad_cmd}")

    def _find_freecad_cmd(self) -> Optional[str]:
        """Try to find FreeCADCmd.exe in common installation locations"""
        # Check environment variable (from .env file or system)
        env_path = os.environ.get('FREECAD_CMD')
        if env_path and os.path.exists(env_path):
            print(f"Found FreeCAD from environment: {env_path}")
            return env_path

        # Common installation paths on Windows
        common_paths = [
            r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD 0.19\bin\FreeCADCmd.exe",
            r"C:\Program Files (x86)\FreeCAD 0.21\bin\FreeCADCmd.exe",
            r"C:\Program Files (x86)\FreeCAD 0.20\bin\FreeCADCmd.exe",
            r"D:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
            r"D:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe",
        ]

        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                print(f"Found FreeCAD at: {path}")
                return path

        print("FreeCADCmd.exe not found. Please install FreeCAD or set FREECAD_CMD environment variable.")
        return None

    def render_to_png(
        self,
        cad_file: str,
        output_png: str,
        width: int = 1920,
        height: int = 1080,
        bg_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> bool:
        """
        Render STEP/IGES file to PNG using FreeCAD

        Args:
            cad_file: Path to STEP/IGES file
            output_png: Path to output PNG file
            width: Image width
            height: Image height
            bg_color: Background color (R, G, B)

        Returns:
            True if successful, False otherwise
        """
        # Create worker script
        worker_script = self._create_worker_script()

        try:
            # Create parameters file
            params = {
                'input_file': str(Path(cad_file).absolute()),
                'output_file': str(Path(output_png).absolute()),
                'width': width,
                'height': height,
                'bg_color': bg_color
            }

            params_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(params, params_file)
            params_file.close()

            # Run FreeCAD
            cmd = [
                self.freecad_cmd,
                '-c',  # Console mode (no GUI)
                worker_script,
                params_file.name
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Increased timeout for larger/complex files
            )

            # Check if output was created
            success = os.path.exists(output_png)

            if not success and result.returncode != 0:
                print(f"FreeCAD error: {result.stderr}")

            return success

        except subprocess.TimeoutExpired:
            print("FreeCAD rendering timed out")
            return False
        except Exception as e:
            print(f"Error during FreeCAD rendering: {e}")
            return False
        finally:
            # Cleanup
            if 'params_file' in locals():
                try:
                    os.unlink(params_file.name)
                except:
                    pass
            try:
                os.unlink(worker_script)
            except:
                pass

    def _create_worker_script(self) -> str:
        """Create temporary Python script for FreeCAD to execute"""
        script_content = '''
import sys
import json
import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
import Part
from PySide2 import QtCore, QtGui

# Initialize GUI even in console mode for rendering
Gui.setupWithoutGUI()

# Read parameters
params_file = sys.argv[1]
with open(params_file, 'r') as f:
    params = json.load(f)

input_file = params['input_file']
output_file = params['output_file']
width = params['width']
height = params['height']
bg_color = params['bg_color']

# Import the CAD file
doc = App.newDocument("CADDoc")
try:
    # Try to import STEP
    if input_file.lower().endswith(('.stp', '.step')):
        Part.insert(input_file, doc.Name)
    # Try to import IGES
    elif input_file.lower().endswith(('.igs', '.iges')):
        Part.insert(input_file, doc.Name)
    else:
        print(f"Unsupported file format: {input_file}")
        sys.exit(1)
except Exception as e:
    print(f"Error importing file: {e}")
    sys.exit(1)

# Create a view
from pivy import coin

# Get all objects
objs = doc.Objects

if not objs:
    print("No objects found in file")
    sys.exit(1)

# Set up the scene graph
root = coin.SoSeparator()
view = Gui.createViewer()

# Add background
bg = coin.SoDirectionalLight()
bg.direction = (0, 0, -1)
root.addChild(bg)

# Add objects to scene
for obj in objs:
    if hasattr(obj, 'ViewObject'):
        root.addChild(obj.ViewObject.RootNode)

view.setSceneGraph(root)
view.setBackgroundColor(coin.SbColor(bg_color[0]/255.0, bg_color[1]/255.0, bg_color[2]/255.0))
view.viewAll()

# Set isometric view
cam = view.getCameraNode()
cam.orientation.setValue(coin.SbRotation(coin.SbVec3f(1, 0, 0), -0.4))
rot = coin.SbRotation(coin.SbVec3f(0, 0, 1), 0.4)
cam.orientation.setValue(cam.orientation.getValue() * rot)

# Render to image
view.resize(width, height)
view.viewAll()

# Save screenshot
img = view.grab()
img.save(output_file, "PNG")

print(f"Rendered to: {output_file}")
App.closeDocument(doc.Name)
'''

        # Write to temporary file
        script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        script_file.write(script_content)
        script_file.close()

        return script_file.name

    def render_with_info_fallback(
        self,
        cad_file: str,
        output_png: str,
        width: int = 1920,
        height: int = 1080
    ) -> bool:
        """
        Try to render with FreeCAD, fallback to info image if fails

        Args:
            cad_file: Path to STEP/IGES file
            output_png: Path to output PNG file
            width: Image width
            height: Image height

        Returns:
            True if successful (either render or fallback)
        """
        # Try FreeCAD rendering first
        success = self.render_to_png(cad_file, output_png, width, height)

        if not success:
            # Create fallback info image
            return self._create_info_image(cad_file, output_png, width, height)

        return True

    def _create_info_image(
        self,
        cad_file: str,
        output_png: str,
        width: int = 1920,
        height: int = 1080
    ) -> bool:
        """Create an info image when rendering fails"""
        try:
            # Create image
            img = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(img)

            # Try to load fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_medium = ImageFont.truetype("arial.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Get file info
            file_path = Path(cad_file)
            file_name = file_path.name
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            file_type = "STEP" if file_path.suffix.lower() in ['.stp', '.step'] else "IGES"

            # Draw content
            y_offset = height // 3

            # Title
            text = f"3D Model ({file_type})"
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, y_offset), text, fill='#333333', font=font_large)
            y_offset += 80

            # File name
            bbox = draw.textbbox((0, 0), file_name, font=font_medium)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, y_offset), file_name, fill='#666666', font=font_medium)
            y_offset += 60

            # File size
            size_text = f"Size: {file_size:.2f} MB"
            bbox = draw.textbbox((0, 0), size_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, y_offset), size_text, fill='#999999', font=font_small)
            y_offset += 50

            # Note about rendering
            note = "3D preview generation in progress..."
            bbox = draw.textbbox((0, 0), note, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((width - text_width) // 2, y_offset), note, fill='#0066cc', font=font_small)

            # Draw border
            draw.rectangle([10, 10, width-11, height-11], outline='#cccccc', width=2)

            # Save image
            img.save(output_png, 'PNG')
            return True

        except Exception as e:
            print(f"Error creating info image: {e}")
            return False

    def extract_geometry_info(self, cad_file: str) -> Optional[Dict]:
        """
        Extract geometry information from CAD file using FreeCAD

        Args:
            cad_file: Path to STEP/IGES file

        Returns:
            Dictionary with geometry info or None if failed
        """
        # Create extraction script
        extract_script = self._create_extract_script()

        try:
            # Create output file for results
            output_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            output_file.close()

            # Run FreeCAD
            cmd = [
                self.freecad_cmd,
                '-c',
                extract_script,
                cad_file,
                output_file.name
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Read results
            if os.path.exists(output_file.name):
                with open(output_file.name, 'r') as f:
                    geometry_info = json.load(f)
                return geometry_info

            return None

        except Exception as e:
            print(f"Error extracting geometry info: {e}")
            return None
        finally:
            # Cleanup
            try:
                os.unlink(extract_script)
                if os.path.exists(output_file.name):
                    os.unlink(output_file.name)
            except:
                pass

    def _create_extract_script(self) -> str:
        """Create script to extract geometry information"""
        script_content = '''
import sys
import json
import FreeCAD as App
import Part

# Get arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# Import the CAD file
doc = App.newDocument("CADDoc")
try:
    Part.insert(input_file, doc.Name)
except Exception as e:
    print(f"Error importing file: {e}")
    sys.exit(1)

# Get all shapes
shapes = []
for obj in doc.Objects:
    if hasattr(obj, 'Shape'):
        shapes.append(obj.Shape)

if not shapes:
    print("No shapes found")
    sys.exit(1)

# Combine all shapes
compound = Part.makeCompound(shapes)

# Get bounding box
bbox = compound.BoundBox

# Extract information
info = {
    'bounding_box': {
        'min_x': bbox.XMin,
        'min_y': bbox.YMin,
        'min_z': bbox.ZMin,
        'max_x': bbox.XMax,
        'max_y': bbox.YMax,
        'max_z': bbox.ZMax,
        'width': bbox.XLength,
        'height': bbox.YLength,
        'depth': bbox.ZLength,
        'diagonal': bbox.DiagonalLength
    },
    'volume': compound.Volume,
    'area': compound.Area,
    'center_of_mass': {
        'x': compound.CenterOfMass.x,
        'y': compound.CenterOfMass.y,
        'z': compound.CenterOfMass.z
    },
    'num_faces': len(compound.Faces),
    'num_edges': len(compound.Edges),
    'num_vertices': len(compound.Vertexes)
}

# Save to file
with open(output_file, 'w') as f:
    json.dump(info, f, indent=2)

App.closeDocument(doc.Name)
'''

        script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        script_file.write(script_content)
        script_file.close()

        return script_file.name


# Convenience function for compatibility with existing code
def process_cad_with_freecad(
    cad_file: str,
    high_res_output: str,
    low_res_output: str,
    freecad_cmd: Optional[str] = None
) -> Tuple[bool, bool]:
    """
    Process CAD file and generate both high-res and low-res images

    Args:
        cad_file: Path to STEP/IGES file
        high_res_output: Path for high-res output
        low_res_output: Path for low-res output
        freecad_cmd: Optional path to FreeCADCmd.exe

    Returns:
        Tuple of (high_res_success, low_res_success)
    """
    try:
        renderer = FreeCADRenderer(freecad_cmd)

        # Generate high-res
        high_success = renderer.render_with_info_fallback(
            cad_file, high_res_output, 1920, 1080
        )

        if high_success and os.path.exists(high_res_output):
            # Create low-res from high-res
            try:
                img = Image.open(high_res_output)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(low_res_output, 'PNG')
                low_success = True
            except Exception as e:
                print(f"Error creating thumbnail: {e}")
                low_success = False
        else:
            low_success = False

        return (high_success, low_success)

    except Exception as e:
        print(f"Error in FreeCAD processing: {e}")
        return (False, False)


if __name__ == "__main__":
    # Test the module
    print("FreeCAD Renderer Test")
    print("=" * 60)

    try:
        renderer = FreeCADRenderer()
        print(f"Found FreeCAD at: {renderer.freecad_cmd}")

        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            if os.path.exists(test_file):
                output_file = "test_render.png"
                print(f"Rendering {test_file} to {output_file}")

                success = renderer.render_with_info_fallback(
                    test_file, output_file, 1920, 1080
                )

                if success:
                    print(f"Success! Output saved to {output_file}")

                    # Try to extract geometry info
                    info = renderer.extract_geometry_info(test_file)
                    if info:
                        print("\nGeometry Information:")
                        print(json.dumps(info, indent=2))
                else:
                    print("Rendering failed!")
            else:
                print(f"File not found: {test_file}")
        else:
            print("Usage: python freecad_renderer.py <cad_file>")

    except Exception as e:
        print(f"Error: {e}")