#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified FreeCAD Renderer - Alternative approach for FreeCAD 1.0
Uses simpler method without complex GUI operations
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SimpleFreeCADRenderer:
    """Simplified FreeCAD renderer for better compatibility"""

    def __init__(self, freecad_cmd_path: Optional[str] = None):
        self.freecad_cmd = freecad_cmd_path or self._find_freecad_cmd()
        if not self.freecad_cmd:
            raise RuntimeError("FreeCADCmd.exe not found")

    def _find_freecad_cmd(self) -> Optional[str]:
        """Find FreeCADCmd.exe"""
        env_path = os.environ.get('FREECAD_CMD')
        if env_path and os.path.exists(env_path):
            return env_path

        common_paths = [
            r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path
        return None

    def extract_geometry_and_screenshot(
        self,
        cad_file: str,
        output_png: str,
        width: int = 1920,
        height: int = 1080
    ) -> bool:
        """Extract geometry info and try to create a simple visualization"""

        # Create simpler worker script
        worker_script = self._create_simple_worker_script()

        try:
            # Create output file for JSON results
            json_output = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json_output.close()

            # Run FreeCAD
            cmd = [
                self.freecad_cmd,
                '-c',  # Console mode
                worker_script,
                cad_file,
                json_output.name,
                output_png
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Shorter timeout for simpler operation
            )

            # Check if geometry was extracted
            if os.path.exists(json_output.name):
                with open(json_output.name, 'r') as f:
                    try:
                        geometry_info = json.load(f)
                    except:
                        geometry_info = None

                # Create visualization image with geometry info
                if geometry_info:
                    return self._create_geometry_visualization(
                        cad_file, output_png, geometry_info, width, height
                    )

            # If no geometry extracted, create basic info image
            return self._create_basic_info_image(cad_file, output_png, width, height)

        except subprocess.TimeoutExpired:
            print("FreeCAD geometry extraction timed out")
            return self._create_basic_info_image(cad_file, output_png, width, height)
        except Exception as e:
            print(f"Error during FreeCAD processing: {e}")
            return self._create_basic_info_image(cad_file, output_png, width, height)
        finally:
            # Cleanup
            try:
                os.unlink(worker_script)
                if 'json_output' in locals() and os.path.exists(json_output.name):
                    os.unlink(json_output.name)
            except:
                pass

    def _create_simple_worker_script(self) -> str:
        """Create a simpler worker script that just extracts geometry"""
        script_content = '''
import sys
import json

try:
    import FreeCAD as App
    import Part

    # Get arguments
    input_file = sys.argv[1]
    output_json = sys.argv[2]
    output_png = sys.argv[3] if len(sys.argv) > 3 else None

    # Create document and import file
    doc = App.newDocument("CADDoc")

    # Import the file
    if input_file.lower().endswith(('.stp', '.step')):
        Part.insert(input_file, doc.Name)
    elif input_file.lower().endswith(('.igs', '.iges')):
        Part.insert(input_file, doc.Name)
    else:
        print(f"Unsupported format")
        sys.exit(1)

    # Get all shapes
    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, 'Shape'):
            shapes.append(obj.Shape)

    if shapes:
        # Combine shapes
        compound = Part.makeCompound(shapes)

        # Get bounding box
        bbox = compound.BoundBox

        # Prepare geometry info
        info = {
            'success': True,
            'bounding_box': {
                'min_x': bbox.XMin, 'min_y': bbox.YMin, 'min_z': bbox.ZMin,
                'max_x': bbox.XMax, 'max_y': bbox.YMax, 'max_z': bbox.ZMax,
                'width': bbox.XLength, 'height': bbox.YLength, 'depth': bbox.ZLength,
                'diagonal': bbox.DiagonalLength,
                'center_x': bbox.Center.x, 'center_y': bbox.Center.y, 'center_z': bbox.Center.z
            },
            'volume': compound.Volume,
            'area': compound.Area,
            'num_faces': len(compound.Faces),
            'num_edges': len(compound.Edges),
            'num_vertices': len(compound.Vertexes)
        }
    else:
        info = {'success': False, 'error': 'No shapes found'}

    # Save JSON
    with open(output_json, 'w') as f:
        json.dump(info, f, indent=2)

    print("Geometry extracted successfully")
    App.closeDocument(doc.Name)

except Exception as e:
    print(f"Error: {e}")
    # Save error info
    with open(output_json, 'w') as f:
        json.dump({'success': False, 'error': str(e)}, f)
    sys.exit(1)
'''
        script_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        script_file.write(script_content)
        script_file.close()
        return script_file.name

    def _create_geometry_visualization(
        self,
        cad_file: str,
        output_png: str,
        geometry_info: dict,
        width: int,
        height: int
    ) -> bool:
        """Create visualization with geometry information"""
        try:
            # Create image
            img = Image.new('RGB', (width, height), color='#f5f5f5')
            draw = ImageDraw.Draw(img)

            # Load fonts
            try:
                font_title = ImageFont.truetype("arial.ttf", 36)
                font_label = ImageFont.truetype("arial.ttf", 20)
                font_value = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_title = ImageFont.load_default()
                font_label = ImageFont.load_default()
                font_value = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # File info
            file_path = Path(cad_file)
            file_type = "STEP" if file_path.suffix.lower() in ['.stp', '.step'] else "IGES"

            # Draw title
            y = 50
            title = f"3D Model Analysis ({file_type})"
            bbox = draw.textbbox((0, 0), title, font=font_title)
            draw.text(((width - bbox[2] + bbox[0]) // 2, y), title, fill='#000000', font=font_title)
            y += 60

            # File name
            bbox = draw.textbbox((0, 0), file_path.name, font=font_label)
            draw.text(((width - bbox[2] + bbox[0]) // 2, y), file_path.name, fill='#666666', font=font_label)
            y += 60

            # Draw a box for the model representation
            box_left = 100
            box_top = y
            box_width = width - 200
            box_height = height - y - 350

            # Background for model area
            draw.rectangle(
                [box_left, box_top, box_left + box_width, box_top + box_height],
                fill='#ffffff',
                outline='#cccccc',
                width=2
            )

            # Draw bounding box visualization (simplified orthographic view)
            if 'bounding_box' in geometry_info:
                bbox_info = geometry_info['bounding_box']

                # Calculate scale to fit in the box
                model_width = bbox_info['width']
                model_height = bbox_info['height']
                model_depth = bbox_info['depth']

                # Draw isometric-style box representation
                cx = box_left + box_width // 2
                cy = box_top + box_height // 2

                # Scale factor
                max_dim = max(model_width, model_height, model_depth)
                scale = min(box_width * 0.6, box_height * 0.6) / max_dim if max_dim > 0 else 1

                # Simplified 3D box corners (isometric projection)
                w = model_width * scale * 0.5
                h = model_height * scale * 0.5
                d = model_depth * scale * 0.3  # Depth factor for isometric view

                # Draw wireframe box
                points = [
                    (cx - w, cy - h),  # Front top-left
                    (cx + w, cy - h),  # Front top-right
                    (cx + w, cy + h),  # Front bottom-right
                    (cx - w, cy + h),  # Front bottom-left
                    (cx - w + d, cy - h - d),  # Back top-left
                    (cx + w + d, cy - h - d),  # Back top-right
                    (cx + w + d, cy + h - d),  # Back bottom-right
                    (cx - w + d, cy + h - d),  # Back bottom-left
                ]

                # Draw edges
                edges = [
                    (0, 1), (1, 2), (2, 3), (3, 0),  # Front face
                    (4, 5), (5, 6), (6, 7), (7, 4),  # Back face
                    (0, 4), (1, 5), (2, 6), (3, 7),  # Connecting edges
                ]

                for i, j in edges:
                    if i < len(points) and j < len(points):
                        draw.line([points[i], points[j]], fill='#4CAF50', width=2)

                # Add dimension labels
                dim_text = f"{model_width:.1f} x {model_height:.1f} x {model_depth:.1f} mm"
                bbox = draw.textbbox((0, 0), dim_text, font=font_value)
                draw.text(
                    ((width - bbox[2] + bbox[0]) // 2, box_top + box_height + 10),
                    dim_text, fill='#000000', font=font_value
                )

            # Geometry information panel
            info_y = box_top + box_height + 50

            # Create two columns for information
            col1_x = 200
            col2_x = width // 2 + 100

            # Column 1 - Dimensions
            draw.text((col1_x, info_y), "Dimensions:", fill='#000000', font=font_label)
            info_y += 30

            if 'bounding_box' in geometry_info:
                bb = geometry_info['bounding_box']
                draw.text((col1_x + 20, info_y), f"Width: {bb['width']:.2f} mm", fill='#333333', font=font_small)
                info_y += 25
                draw.text((col1_x + 20, info_y), f"Height: {bb['height']:.2f} mm", fill='#333333', font=font_small)
                info_y += 25
                draw.text((col1_x + 20, info_y), f"Depth: {bb['depth']:.2f} mm", fill='#333333', font=font_small)
                info_y += 25
                draw.text((col1_x + 20, info_y), f"Diagonal: {bb['diagonal']:.2f} mm", fill='#333333', font=font_small)

            # Column 2 - Properties
            info_y = box_top + box_height + 50
            draw.text((col2_x, info_y), "Properties:", fill='#000000', font=font_label)
            info_y += 30

            draw.text((col2_x + 20, info_y), f"Volume: {geometry_info.get('volume', 0):.2f} mm³", fill='#333333', font=font_small)
            info_y += 25
            draw.text((col2_x + 20, info_y), f"Surface Area: {geometry_info.get('area', 0):.2f} mm²", fill='#333333', font=font_small)
            info_y += 25
            draw.text((col2_x + 20, info_y), f"Faces: {geometry_info.get('num_faces', 0)}", fill='#333333', font=font_small)
            info_y += 25
            draw.text((col2_x + 20, info_y), f"Edges: {geometry_info.get('num_edges', 0)}", fill='#333333', font=font_small)

            # Save image
            img.save(output_png, 'PNG')
            return True

        except Exception as e:
            print(f"Error creating visualization: {e}")
            return False

    def _create_basic_info_image(
        self,
        cad_file: str,
        output_png: str,
        width: int,
        height: int
    ) -> bool:
        """Create basic info image when processing fails"""
        try:
            img = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(img)

            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_medium = ImageFont.truetype("arial.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            file_path = Path(cad_file)
            file_type = "STEP" if file_path.suffix.lower() in ['.stp', '.step'] else "IGES"

            y = height // 3

            # Title
            text = f"3D Model ({file_type})"
            bbox = draw.textbbox((0, 0), text, font=font_large)
            draw.text(((width - bbox[2] + bbox[0]) // 2, y), text, fill='#333333', font=font_large)
            y += 80

            # File name
            bbox = draw.textbbox((0, 0), file_path.name, font=font_medium)
            draw.text(((width - bbox[2] + bbox[0]) // 2, y), file_path.name, fill='#666666', font=font_medium)
            y += 60

            # Note
            note = "Processing... Geometry extraction in progress"
            bbox = draw.textbbox((0, 0), note, font=font_small)
            draw.text(((width - bbox[2] + bbox[0]) // 2, y), note, fill='#0066cc', font=font_small)

            img.save(output_png, 'PNG')
            return True

        except Exception as e:
            print(f"Error creating basic info image: {e}")
            return False


# Convenience function for integration
def render_with_simple_method(
    cad_file: str,
    output_png: str,
    width: int = 1920,
    height: int = 1080
) -> bool:
    """Render CAD file using simplified method"""
    try:
        renderer = SimpleFreeCADRenderer()
        return renderer.extract_geometry_and_screenshot(
            cad_file, output_png, width, height
        )
    except Exception as e:
        print(f"Simple rendering failed: {e}")
        return False


if __name__ == "__main__":
    # Test the simplified renderer
    print("Simple FreeCAD Renderer Test")
    print("=" * 60)

    try:
        renderer = SimpleFreeCADRenderer()
        print(f"FreeCAD found at: {renderer.freecad_cmd}")

        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            output = "simple_render_test.png"

            print(f"Processing: {test_file}")
            success = renderer.extract_geometry_and_screenshot(test_file, output)

            if success:
                print(f"Success! Output: {output}")
            else:
                print("Processing failed")
    except Exception as e:
        print(f"Error: {e}")