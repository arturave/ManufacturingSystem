#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD File Processing Utilities
Handles DXF, DWG, and 3D file processing (STEP, STP, IGS, IGES)
Generates preview images from CAD files
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

# Try to import ezdxf with PyMuPDF backend for better rendering
try:
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend, config, layout
    # Try PyMuPDF backend first for better quality
    try:
        import pymupdf
        from ezdxf.addons.drawing.pymupdf import PyMuPdfBackend
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

    # Always import matplotlib backend as fallback
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    PYMUPDF_AVAILABLE = False
    print("Warning: ezdxf not installed. DXF/DWG processing will not be available.")

# Try to import OCC for 3D file processing (optional)
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IGESControl import IGESControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone
    from OCC.Core.BRepBndLib import brepbndlib_Add
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Extend.DataExchange import read_step_file, read_iges_file
    from OCC.Display import SimpleGui
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False
    print("Warning: pythonocc-core not installed. 3D file processing will not be available.")

# Supported file formats
DXF_FORMATS = {'.dxf', '.dwg'}
STEP_FORMATS = {'.step', '.stp'}
IGES_FORMATS = {'.igs', '.iges'}
CAD_3D_FORMATS = STEP_FORMATS | IGES_FORMATS
ALL_CAD_FORMATS = DXF_FORMATS | CAD_3D_FORMATS


class CADProcessor:
    """Handles CAD file processing and preview generation"""

    @staticmethod
    def is_cad_file(file_path: str) -> bool:
        """Check if file is a supported CAD format"""
        ext = Path(file_path).suffix.lower()
        return ext in ALL_CAD_FORMATS

    @staticmethod
    def is_dxf_file(file_path: str) -> bool:
        """Check if file is DXF/DWG"""
        ext = Path(file_path).suffix.lower()
        return ext in DXF_FORMATS

    @staticmethod
    def is_3d_file(file_path: str) -> bool:
        """Check if file is 3D CAD format"""
        ext = Path(file_path).suffix.lower()
        return ext in CAD_3D_FORMATS

    @staticmethod
    def get_file_type(file_path: str) -> Optional[str]:
        """Get CAD file type"""
        ext = Path(file_path).suffix.lower()
        if ext in DXF_FORMATS:
            return 'dxf'
        elif ext in STEP_FORMATS:
            return 'step'
        elif ext in IGES_FORMATS:
            return 'iges'
        return None

    @staticmethod
    def process_dxf_to_image(
        dxf_path: str,
        output_path: str,
        dpi: int = 300
    ) -> bool:
        """
        Convert DXF file to PNG image using ezdxf with PyMuPDF backend
        Based on: https://ezdxf.readthedocs.io/en/stable/tutorials/image_export.html

        Args:
            dxf_path: Path to DXF file
            output_path: Path to save output PNG image
            dpi: Resolution in DPI (default 300 for high quality)

        Returns:
            True if successful, False otherwise
        """
        if not EZDXF_AVAILABLE:
            print("Error: ezdxf not available. Cannot process DXF files.")
            return False

        temp_dxf_path = None
        try:
            # Handle DWG files by converting to DXF first (if ODA converter is available)
            ext = Path(dxf_path).suffix.lower()
            if ext == '.dwg':
                temp_dxf = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
                temp_dxf_path = temp_dxf.name
                temp_dxf.close()

                # Try to convert DWG to DXF using ODA File Converter
                oda_converter = r"C:\Program Files\ODA\ODAFileConverter 26.4.0\ODAFileConverter.exe"
                if os.path.exists(oda_converter):
                    try:
                        input_dir = str(Path(dxf_path).parent)
                        output_dir = str(Path(temp_dxf_path).parent)
                        subprocess.run([
                            oda_converter,
                            input_dir,
                            output_dir,
                            "ACAD2018",  # Output version
                            "DXF",       # Output format
                            "0",         # Recurse
                            "1",         # Audit
                            str(Path(dxf_path).name)
                        ], check=True, capture_output=True, timeout=30)
                        dxf_path = temp_dxf_path
                    except Exception as e:
                        print(f"Warning: Could not convert DWG to DXF: {e}")
                        if temp_dxf_path and os.path.exists(temp_dxf_path):
                            os.unlink(temp_dxf_path)
                        return False
                else:
                    print("Warning: ODA File Converter not found. Cannot process DWG files.")
                    if temp_dxf_path and os.path.exists(temp_dxf_path):
                        os.unlink(temp_dxf_path)
                    return False

            # Read DXF file
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # Get drawing extents to calculate proper page size
            try:
                extents = msp.extents()
                # Calculate size in mm from drawing units
                width_mm = abs(extents.extmax.x - extents.extmin.x)
                height_mm = abs(extents.extmax.y - extents.extmin.y)

                # Ensure minimum size and add margins
                width_mm = max(width_mm, 100) * 1.1
                height_mm = max(height_mm, 100) * 1.1
            except:
                # If extents cannot be calculated, use A4 size
                width_mm = 297  # A4 landscape
                height_mm = 210

            if PYMUPDF_AVAILABLE:
                # Use PyMuPDF backend for better quality
                try:
                    # Step 1: Create render context
                    ctx = RenderContext(doc)

                    # Step 2: Configure rendering
                    cfg = config.Configuration(
                        background_policy=config.BackgroundPolicy.WHITE,
                        color_policy=config.ColorPolicy.BLACK,
                        lineweight_scaling=1.0,
                        min_lineweight=0.24,
                    )

                    # Step 3: Instantiate backend
                    backend = PyMuPdfBackend()

                    # Step 4: Configure frontend and draw
                    frontend = Frontend(ctx, backend, config=cfg)
                    frontend.draw_layout(msp, finalize=True)

                    # Step 5: Setup page layout with proper dimensions
                    page = layout.Page(
                        width_mm,
                        height_mm,
                        layout.Units.mm,
                        margins=layout.Margins.all(2)
                    )

                    # Step 6: Get PDF bytes and convert to PNG
                    pdf_bytes = backend.get_pdf_bytes(page)

                    # Open PDF from bytes
                    pdf_doc = pymupdf.open("pdf", pdf_bytes)

                    # Get first page
                    pdf_page = pdf_doc[0]

                    # Calculate zoom for desired DPI
                    # PyMuPDF uses 72 DPI as base
                    zoom = dpi / 72.0
                    mat = pymupdf.Matrix(zoom, zoom)

                    # Render to pixmap
                    pix = pdf_page.get_pixmap(matrix=mat, alpha=False)

                    # Save as PNG
                    pix.save(output_path)

                    # Cleanup
                    pdf_doc.close()

                    # Clean up temporary DXF if it was created from DWG
                    if temp_dxf_path and os.path.exists(temp_dxf_path):
                        try:
                            os.unlink(temp_dxf_path)
                        except:
                            pass

                    return True

                except Exception as e:
                    print(f"PyMuPDF rendering failed: {e}, falling back to matplotlib")
                    # Fallback to matplotlib
                    result = CADProcessor._process_dxf_with_matplotlib(doc, msp, output_path, (1920, 1080))
                    if temp_dxf_path and os.path.exists(temp_dxf_path):
                        try:
                            os.unlink(temp_dxf_path)
                        except:
                            pass
                    return result
            else:
                # Use matplotlib backend as fallback
                result = CADProcessor._process_dxf_with_matplotlib(doc, msp, output_path, (1920, 1080))
                if temp_dxf_path and os.path.exists(temp_dxf_path):
                    try:
                        os.unlink(temp_dxf_path)
                    except:
                        pass
                return result

        except Exception as e:
            print(f"Error processing DXF file {dxf_path}: {e}")
            import traceback
            traceback.print_exc()
            # Clean up temporary file on error
            if temp_dxf_path and os.path.exists(temp_dxf_path):
                try:
                    os.unlink(temp_dxf_path)
                except:
                    pass
            return False

    @staticmethod
    def _process_dxf_with_matplotlib(doc, msp, output_path: str, image_size: Tuple[int, int]) -> bool:
        """Fallback method using matplotlib backend"""
        try:
            # Create matplotlib figure
            fig = plt.figure(figsize=(image_size[0]/100, image_size[1]/100), dpi=100)
            ax = fig.add_axes([0, 0, 1, 1])

            # Setup rendering context
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)

            # Render DXF
            Frontend(ctx, out).draw_layout(msp, finalize=True)

            # Remove axes
            ax.set_axis_off()
            ax.set_aspect('equal')

            # Save figure
            plt.savefig(output_path, dpi=100, bbox_inches='tight', pad_inches=0.1,
                       facecolor='white', edgecolor='none')
            plt.close(fig)

            return True

        except Exception as e:
            print(f"Error processing DXF: {e}")
            return False

    @staticmethod
    def process_step_to_image(
        step_path: str,
        output_path: str,
        image_size: Tuple[int, int] = (1920, 1080)
    ) -> bool:
        """
        Convert STEP file to image preview using render3d module

        Args:
            step_path: Path to STEP file
            output_path: Path to save output image
            image_size: Output image size (width, height)

        Returns:
            True if successful, False otherwise
        """
        # Try to use the new render3d module first
        try:
            from render3d import StepIgesRenderer, OCC_AVAILABLE as RENDER3D_AVAILABLE

            if RENDER3D_AVAILABLE:
                try:
                    renderer = StepIgesRenderer(width=image_size[0], height=image_size[1])
                    # Try full rendering first
                    try:
                        renderer.render_to_png(step_path, output_path)
                        return True
                    except Exception as render_err:
                        print(f"Full 3D rendering failed: {render_err}, trying fallback...")
                        # Use fallback method that creates info image
                        renderer.render_to_png_fallback(step_path, output_path)
                        return True

                except Exception as e:
                    print(f"Error using render3d module: {e}")
                    # Fall through to old method
            else:
                print("render3d module available but OCC not installed")

        except ImportError:
            print("render3d module not available, using legacy method")

        # Fallback to old method if render3d is not available or fails
        if not OCC_AVAILABLE:
            print("Warning: pythonocc-core not available. Creating placeholder for STEP file.")
            return CADProcessor._create_3d_placeholder(step_path, output_path, "STEP")

        try:
            # Read STEP file
            shape = read_step_file(step_path)
            if shape is None:
                print(f"Error: Could not read STEP file {step_path}")
                return False

            # Create screenshot (simplified approach - would need proper 3D rendering in production)
            # For now, create a placeholder with file info
            return CADProcessor._create_3d_info_image(step_path, output_path, "STEP", shape)

        except Exception as e:
            print(f"Error processing STEP file {step_path}: {e}")
            return CADProcessor._create_3d_placeholder(step_path, output_path, "STEP")

    @staticmethod
    def process_iges_to_image(
        iges_path: str,
        output_path: str,
        image_size: Tuple[int, int] = (1920, 1080)
    ) -> bool:
        """
        Convert IGES file to image preview using render3d module

        Args:
            iges_path: Path to IGES file
            output_path: Path to save output image
            image_size: Output image size (width, height)

        Returns:
            True if successful, False otherwise
        """
        # Try to use the new render3d module first
        try:
            from render3d import StepIgesRenderer, OCC_AVAILABLE as RENDER3D_AVAILABLE

            if RENDER3D_AVAILABLE:
                try:
                    renderer = StepIgesRenderer(width=image_size[0], height=image_size[1])
                    # Try full rendering first
                    try:
                        renderer.render_to_png(iges_path, output_path)
                        return True
                    except Exception as render_err:
                        print(f"Full 3D rendering failed: {render_err}, trying fallback...")
                        # Use fallback method that creates info image
                        renderer.render_to_png_fallback(iges_path, output_path)
                        return True

                except Exception as e:
                    print(f"Error using render3d module: {e}")
                    # Fall through to old method
            else:
                print("render3d module available but OCC not installed")

        except ImportError:
            print("render3d module not available, using legacy method")

        # Fallback to old method if render3d is not available or fails
        if not OCC_AVAILABLE:
            print("Warning: pythonocc-core not available. Creating placeholder for IGES file.")
            return CADProcessor._create_3d_placeholder(iges_path, output_path, "IGES")

        try:
            # Read IGES file
            shape = read_iges_file(iges_path)
            if shape is None:
                print(f"Error: Could not read IGES file {iges_path}")
                return False

            # Create screenshot (simplified approach)
            return CADProcessor._create_3d_info_image(iges_path, output_path, "IGES", shape)

        except Exception as e:
            print(f"Error processing IGES file {iges_path}: {e}")
            return CADProcessor._create_3d_placeholder(iges_path, output_path, "IGES")

    @staticmethod
    def _create_3d_placeholder(
        file_path: str,
        output_path: str,
        file_type: str
    ) -> bool:
        """Create placeholder image for 3D files when OCC is not available"""
        try:
            # Create a simple placeholder image
            img = Image.new('RGB', (800, 600), color='#2b2b2b')
            draw = ImageDraw.Draw(img)

            try:
                font_large = ImageFont.truetype("arial.ttf", 32)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Get file info
            file_name = Path(file_path).name
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            # Draw placeholder content
            y_offset = 200

            # Title
            text = f"Plik {file_type}"
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox[2] - bbox[0]
            draw.text(((800 - text_width) // 2, y_offset), text, fill='#ffffff', font=font_large)
            y_offset += 60

            # File name
            bbox = draw.textbbox((0, 0), file_name, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((800 - text_width) // 2, y_offset), file_name, fill='#cccccc', font=font_small)
            y_offset += 40

            # File size
            size_text = f"Rozmiar: {file_size_mb:.2f} MB"
            bbox = draw.textbbox((0, 0), size_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((800 - text_width) // 2, y_offset), size_text, fill='#999999', font=font_small)
            y_offset += 40

            # Note
            note = "Podgląd 3D niedostępny"
            bbox = draw.textbbox((0, 0), note, font=font_small)
            text_width = bbox[2] - bbox[0]
            draw.text(((800 - text_width) // 2, y_offset), note, fill='#666666', font=font_small)

            # Save image
            img.save(output_path, 'PNG')
            return True

        except Exception as e:
            print(f"Error creating placeholder for {file_path}: {e}")
            return False

    @staticmethod
    def _create_3d_info_image(
        file_path: str,
        output_path: str,
        file_type: str,
        shape
    ) -> bool:
        """Create info image with bounding box for 3D files"""
        try:
            # Get bounding box
            bbox = Bnd_Box()
            brepbndlib_Add(shape, bbox)
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

            # Calculate dimensions
            width = xmax - xmin
            height = ymax - ymin
            depth = zmax - zmin

            # Create image with info
            img = Image.new('RGB', (800, 600), color='#2b2b2b')
            draw = ImageDraw.Draw(img)

            try:
                font_large = ImageFont.truetype("arial.ttf", 28)
                font_medium = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            file_name = Path(file_path).name
            y_offset = 150

            # Title
            text = f"Model 3D ({file_type})"
            bbox_text = draw.textbbox((0, 0), text, font=font_large)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), text, fill='#ffffff', font=font_large)
            y_offset += 50

            # File name
            bbox_text = draw.textbbox((0, 0), file_name, font=font_small)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), file_name, fill='#cccccc', font=font_small)
            y_offset += 60

            # Dimensions
            dims_text = "Wymiary gabarytu:"
            bbox_text = draw.textbbox((0, 0), dims_text, font=font_medium)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), dims_text, fill='#00ff00', font=font_medium)
            y_offset += 40

            # Width
            text = f"Szerokość: {width:.2f} mm"
            bbox_text = draw.textbbox((0, 0), text, font=font_small)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), text, fill='#ffffff', font=font_small)
            y_offset += 30

            # Height
            text = f"Wysokość: {height:.2f} mm"
            bbox_text = draw.textbbox((0, 0), text, font=font_small)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), text, fill='#ffffff', font=font_small)
            y_offset += 30

            # Depth
            text = f"Głębokość: {depth:.2f} mm"
            bbox_text = draw.textbbox((0, 0), text, font=font_small)
            text_width = bbox_text[2] - bbox_text[0]
            draw.text(((800 - text_width) // 2, y_offset), text, fill='#ffffff', font=font_small)

            # Save
            img.save(output_path, 'PNG')
            return True

        except Exception as e:
            print(f"Error creating 3D info image: {e}")
            return CADProcessor._create_3d_placeholder(file_path, output_path, file_type)

    @staticmethod
    def process_cad_file(
        cad_path: str,
        output_path: str,
        dpi: int = 300
    ) -> bool:
        """
        Process any supported CAD file and generate preview image

        Args:
            cad_path: Path to CAD file
            output_path: Path to save output PNG image
            dpi: Resolution in DPI (default 300 for high quality)

        Returns:
            True if successful, False otherwise
        """
        file_type = CADProcessor.get_file_type(cad_path)

        if file_type == 'dxf':
            return CADProcessor.process_dxf_to_image(cad_path, output_path, dpi)
        elif file_type == 'step':
            return CADProcessor.process_step_to_image(cad_path, output_path, (1920, 1080))
        elif file_type == 'iges':
            return CADProcessor.process_iges_to_image(cad_path, output_path, (1920, 1080))
        else:
            print(f"Unsupported CAD file type: {file_type}")
            return False

    @staticmethod
    def process_cad_file_both_resolutions(
        cad_path: str,
        high_res_output: str,
        low_res_output: str
    ) -> Tuple[bool, bool]:
        """
        Process CAD file and generate both high-res and low-res preview images

        Args:
            cad_path: Path to CAD file
            high_res_output: Path to save high-resolution PNG (300 DPI)
            low_res_output: Path to save low-resolution PNG (72 DPI)

        Returns:
            Tuple of (high_res_success, low_res_success)
        """
        file_type = CADProcessor.get_file_type(cad_path)

        if file_type == 'dxf':
            # Generate high-res version (300 DPI)
            high_res_success = CADProcessor.process_dxf_to_image(cad_path, high_res_output, dpi=300)

            # Generate low-res version (72 DPI) - good for thumbnails
            low_res_success = CADProcessor.process_dxf_to_image(cad_path, low_res_output, dpi=72)

            return (high_res_success, low_res_success)

        elif file_type in ['step', 'iges']:
            # For 3D files, generate one image and resize
            temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_image.name
            temp_image.close()

            if file_type == 'step':
                success = CADProcessor.process_step_to_image(cad_path, temp_path, (1920, 1080))
            else:
                success = CADProcessor.process_iges_to_image(cad_path, temp_path, (1920, 1080))

            if success:
                # Use PIL to create high-res and low-res versions
                try:
                    from PIL import Image

                    img = Image.open(temp_path)

                    # Save high-res
                    img.save(high_res_output, 'PNG')

                    # Create low-res (200x200 thumbnail)
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    img.save(low_res_output, 'PNG')

                    # Clean up temp file
                    os.unlink(temp_path)

                    return (True, True)
                except Exception as e:
                    print(f"Error creating resolutions: {e}")
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    return (False, False)
            else:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return (False, False)

        else:
            print(f"Unsupported CAD file type: {file_type}")
            return (False, False)

    @staticmethod
    def extract_dxf_info(dxf_path: str) -> dict:
        """
        Extract metadata and information from DXF file

        Args:
            dxf_path: Path to DXF file

        Returns:
            Dictionary with DXF information
        """
        if not EZDXF_AVAILABLE:
            return {'error': 'ezdxf not available'}

        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            # Count entities
            entity_counts = {}
            for entity in msp:
                entity_type = entity.dxftype()
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

            # Get layer names
            layers = [layer.dxf.name for layer in doc.layers]

            # Get extents (bounding box)
            try:
                extents = msp.extents()
                bbox = {
                    'min_x': extents.extmin.x,
                    'min_y': extents.extmin.y,
                    'max_x': extents.extmax.x,
                    'max_y': extents.extmax.y,
                    'width': extents.extmax.x - extents.extmin.x,
                    'height': extents.extmax.y - extents.extmin.y
                }
            except:
                bbox = None

            return {
                'version': doc.dxfversion,
                'layers': layers,
                'entity_counts': entity_counts,
                'total_entities': sum(entity_counts.values()),
                'bounding_box': bbox
            }

        except Exception as e:
            print(f"Error extracting DXF info from {dxf_path}: {e}")
            return {'error': str(e)}


def get_cad_file_info(file_path: str) -> dict:
    """
    Get information about a CAD file

    Args:
        file_path: Path to CAD file

    Returns:
        Dictionary with file information
    """
    info = {
        'file_name': Path(file_path).name,
        'file_size': os.path.getsize(file_path),
        'file_type': CADProcessor.get_file_type(file_path)
    }

    # Add type-specific info
    if info['file_type'] == 'dxf':
        dxf_info = CADProcessor.extract_dxf_info(file_path)
        info.update(dxf_info)

    return info
