#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render3d.py
STEP/IGES -> PNG + thumbnail -> upload to Supabase
2025-10 | v1.0

This module provides 3D CAD file rendering functionality for the ManufacturingSystem.
It converts STEP and IGES files to PNG images with isometric view and creates thumbnails.
Optionally uploads to Supabase storage.
"""

from __future__ import annotations
import os
import io
import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from pathlib import Path

# --- OCC / OpenCascade (pythonOCC-core) ---
try:
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IGESControl import IGESControl_Reader
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Display.SimpleGui import init_display
    from OCC.Core.Graphic3d import Graphic3d_RenderingMode
    OCC_AVAILABLE = True
except ImportError:
    OCC_AVAILABLE = False
    print("Warning: pythonocc-core not installed. 3D rendering will not be available.")
    print("Install with: conda install -c conda-forge pythonocc-core")

# --- Imaging ---
from PIL import Image

# --- Supabase (optional) ---
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Note: supabase-py not installed. Upload functionality will not be available.")

# --- Utils ---
def _ext_ok(p: Path) -> bool:
    """Check if file extension is supported"""
    return p.suffix.lower() in (".stp", ".step", ".igs", ".iges")

def _sha1(path: Path) -> str:
    """Generate SHA1 hash for file (first 12 chars)"""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

@dataclass
class RenderOutputs:
    """Container for render output information"""
    png_path: Path
    thumb_path: Path
    width: int
    height: int
    bounding_box: Optional[Dict] = None

class StepIgesRenderer:
    """
    Minimal 3D renderer (OpenCascade -> pythonOCC) for static images.
    Creates isometric projection on white background with shaded rendering.
    """

    def __init__(self, width: int = 1000, height: int = 800, bg=(255, 255, 255)):
        self.width = width
        self.height = height
        self.bg = bg

    def _read_shape(self, model_path: Path):
        """Read 3D shape from STEP or IGES file"""
        ext = model_path.suffix.lower()

        if ext in (".stp", ".step"):
            reader = STEPControl_Reader()
            status = reader.ReadFile(str(model_path))
            if status != 1:  # Use numeric check as in user's version
                raise RuntimeError(f"STEP read error: status={status}")
            reader.TransferRoots()
            shape = reader.OneShape()
            return shape

        elif ext in (".igs", ".iges"):
            reader = IGESControl_Reader()
            status = reader.ReadFile(str(model_path))
            if status != 1:  # Use numeric check as in user's version
                raise RuntimeError(f"IGES read error: status={status}")
            reader.TransferRoots()
            shape = reader.OneShape()
            return shape

        else:
            raise ValueError(f"Unsupported extension: {ext}")

    def _get_bounding_box(self, shape) -> Dict:
        """Calculate bounding box dimensions for the shape"""
        try:
            from OCC.Core.BRepBndLib import brepbndlib
            bbox = Bnd_Box()
            brepbndlib.Add(shape, bbox)
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

            return {
                'min_x': xmin, 'min_y': ymin, 'min_z': zmin,
                'max_x': xmax, 'max_y': ymax, 'max_z': zmax,
                'width': xmax - xmin,
                'height': ymax - ymin,
                'depth': zmax - zmin
            }
        except Exception as e:
            print(f"Error calculating bounding box: {e}")
            return None

    def render_to_png(self, src: str | Path, out_png: str | Path,
                     headless: bool = False) -> RenderOutputs:
        """
        Render STEP/IGES file to PNG with isometric view and white background.

        Args:
            src: Path to STEP/IGES file
            out_png: Path to output PNG file
            headless: If True, use virtual display (for servers)

        Returns:
            RenderOutputs with paths and dimensions
        """
        if not OCC_AVAILABLE:
            raise RuntimeError("pythonocc-core is not installed")

        model_path = Path(src)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {src}")
        if not _ext_ok(model_path):
            raise ValueError("Supported: .stp, .step, .igs, .iges")

        shape = self._read_shape(model_path)
        bbox = self._get_bounding_box(shape)

        # Setup virtual display for headless rendering (Linux servers)
        if headless:
            import os
            os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":0")
            # Run with: xvfb-run -a python your_script.py

        # Initialize display - simplified version
        display, start_display, add_menu, add_function_to_menu = init_display()

        # Display shape
        display.DisplayShape(shape, update=True)

        # Set isometric view
        display.View.SetProj(1, 1, 1)

        # Set background color
        display.View.SetBackgroundColor(*self.bg)
        display.View.SetSize(self.width, self.height)

        # Apply shaded rendering mode using Graphic3d
        try:
            display.View.SetRenderingMode(Graphic3d_RenderingMode.Graphic3d_RM_SHADED)
        except:
            # Fallback to default shaded mode
            display.SetModeShaded()

        display.View.MustBeResized()
        display.FitAll()

        # Save to file
        out_png = Path(out_png)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        display.View.Dump(str(out_png))

        return RenderOutputs(
            png_path=out_png,
            thumb_path=out_png,
            width=self.width,
            height=self.height,
            bounding_box=bbox
        )

    def render_to_png_fallback(self, src: str | Path, out_png: str | Path) -> RenderOutputs:
        """
        Fallback method that creates an info image when rendering fails.
        This is useful when OCC display initialization fails.
        """
        model_path = Path(src)

        # Try to get bounding box if possible
        bbox = None
        if OCC_AVAILABLE:
            try:
                shape = self._read_shape(model_path)
                bbox = self._get_bounding_box(shape)
            except:
                pass

        # Create info image with bounding box data
        img = Image.new('RGB', (self.width, self.height), color=self.bg)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype("arial.ttf", 32)
            font_medium = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw info
        y = 100
        file_type = "STEP" if model_path.suffix.lower() in (".stp", ".step") else "IGES"

        texts = [
            (f"3D Model ({file_type})", font_large, '#000000'),
            ("", None, None),
            (f"File: {model_path.name}", font_medium, '#333333'),
            ("", None, None),
            ("Bounding Box:", font_medium, '#000000'),
        ]

        if bbox:
            texts.extend([
                (f"Width: {bbox['width']:.2f} mm", font_small, '#666666'),
                (f"Height: {bbox['height']:.2f} mm", font_small, '#666666'),
                (f"Depth: {bbox['depth']:.2f} mm", font_small, '#666666'),
            ])
        else:
            texts.append(("Dimensions not available", font_small, '#999999'))

        for text, font, color in texts:
            if text and font:
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), text, fill=color, font=font)
                y += text_bbox[3] - text_bbox[1] + 10
            else:
                y += 20

        # Save
        out_png = Path(out_png)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_png, 'PNG')

        return RenderOutputs(
            png_path=out_png,
            thumb_path=out_png,
            width=self.width,
            height=self.height,
            bounding_box=bbox
        )

class Thumbnailer:
    """
    Creates PNG thumbnails with preserved aspect ratio.
    """

    def __init__(self, size: Tuple[int, int] = (320, 240)):
        self.size = size

    def make_thumbnail(self, src_png: str | Path, thumb_out: str | Path) -> Path:
        """Create thumbnail from PNG image"""
        src_png = Path(src_png)
        thumb_out = Path(thumb_out)

        with Image.open(src_png) as im:
            im = im.convert("RGB")
            im.thumbnail(self.size, Image.LANCZOS)
            thumb_out.parent.mkdir(parents=True, exist_ok=True)
            im.save(thumb_out, format="PNG")

        return thumb_out

class SupabaseUploader:
    """
    Simple wrapper for supabase-py to upload files to Storage bucket.
    """

    def __init__(self, url: str, key: str, bucket: str = "attachments"):
        if not SUPABASE_AVAILABLE:
            raise RuntimeError("supabase-py is not installed")

        self.url = url
        self.key = key
        self.bucket = bucket
        self.client: Client = create_client(self.url, self.key)

    def upload_file(self, local_path: str | Path, dest_path: str,
                   upsert: bool = True) -> Dict:
        """Upload file to Supabase storage"""
        local_path = Path(local_path)

        with open(local_path, "rb") as f:
            res = self.client.storage.from_(self.bucket).upload(
                file=f,
                path=dest_path,
                file_options={"content-type": "image/png", "upsert": upsert}
            )

        # Get public URL (if bucket is public or policy allows)
        public_url = self.client.storage.from_(self.bucket).get_public_url(dest_path)

        return {"path": dest_path, "public_url": public_url}

# === High-level API ==========================================================

def generate_and_upload(
    model_path: str,
    supabase_url: str,
    supabase_key: str,
    part_id: str | int,
    order_process_no: Optional[str] = None,
    bucket: str = "attachments",
    images_root_prefix: str = "parts",
    render_size: Tuple[int, int] = (1200, 900),
    thumb_size: Tuple[int, int] = (360, 270)
) -> Dict:
    """
    Main function: STEP/IGES -> PNG + thumbnail -> upload to Supabase.
    Returns dictionary with public URLs and Storage paths.

    Args:
        model_path: Path to .stp/.step/.igs/.iges file
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        part_id: Part ID (UUID or int)
        order_process_no: Optional order process number (e.g., '2025-00042')
        bucket: Storage bucket name
        images_root_prefix: Prefix in Storage (e.g., 'parts')
        render_size: Size for full render
        thumb_size: Size for thumbnail

    Returns:
        Dictionary with local and remote paths/URLs
    """
    if not SUPABASE_AVAILABLE:
        raise RuntimeError("supabase-py is not installed")

    src = Path(model_path)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {model_path}")
    if not _ext_ok(src):
        raise ValueError("Supported: .stp, .step, .igs, .iges")

    # Local outputs (temporary or cache directory)
    sha = _sha1(src)
    out_dir = Path(".cache_renders") / sha
    out_dir.mkdir(parents=True, exist_ok=True)

    full_png = out_dir / f"{src.stem}_full.png"
    thumb_png = out_dir / f"{src.stem}_thumb.png"

    # 1) Render
    renderer = StepIgesRenderer(width=render_size[0], height=render_size[1])
    try:
        outputs = renderer.render_to_png(src, full_png)
    except Exception as e:
        print(f"Render failed, using fallback: {e}")
        outputs = renderer.render_to_png_fallback(src, full_png)

    # 2) Thumbnail
    thumb = Thumbnailer(size=thumb_size)
    thumb.make_thumbnail(full_png, thumb_png)

    # 3) Upload to Supabase
    uploader = SupabaseUploader(supabase_url, supabase_key, bucket=bucket)

    # Storage path, e.g., attachments/parts/<part_id>/...
    # Optionally add order_process_no:
    if order_process_no:
        prefix = f"{images_root_prefix}/{order_process_no}/part_{part_id}"
    else:
        prefix = f"{images_root_prefix}/part_{part_id}"

    dest_full = f"{prefix}/{full_png.name}"
    dest_thumb = f"{prefix}/{thumb_png.name}"

    up_full = uploader.upload_file(full_png, dest_full, upsert=True)
    up_thumb = uploader.upload_file(thumb_png, dest_thumb, upsert=True)

    return {
        "full_png_local": str(full_png),
        "thumb_png_local": str(thumb_png),
        "full_png_storage_path": up_full["path"],
        "thumb_png_storage_path": up_thumb["path"],
        "full_png_url": up_full["public_url"],
        "thumb_png_url": up_thumb["public_url"],
        "bounding_box": outputs.bounding_box
    }

def generate_local_only(
    model_path: str,
    output_dir: str = None,
    render_size: Tuple[int, int] = (1200, 900),
    thumb_size: Tuple[int, int] = (360, 270)
) -> Dict:
    """
    Generate PNG and thumbnail locally without uploading to Supabase.
    Useful for local testing or when Supabase is not configured.

    Args:
        model_path: Path to .stp/.step/.igs/.iges file
        output_dir: Directory to save outputs (default: temp directory)
        render_size: Size for full render
        thumb_size: Size for thumbnail

    Returns:
        Dictionary with local paths and bounding box info
    """
    src = Path(model_path)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {model_path}")
    if not _ext_ok(src):
        raise ValueError("Supported: .stp, .step, .igs, .iges")

    # Output directory
    if output_dir:
        out_dir = Path(output_dir)
    else:
        import tempfile
        out_dir = Path(tempfile.mkdtemp(prefix="render3d_"))

    out_dir.mkdir(parents=True, exist_ok=True)

    full_png = out_dir / f"{src.stem}_full.png"
    thumb_png = out_dir / f"{src.stem}_thumb.png"

    # 1) Render
    renderer = StepIgesRenderer(width=render_size[0], height=render_size[1])
    try:
        outputs = renderer.render_to_png(src, full_png)
    except Exception as e:
        print(f"Render failed, using fallback: {e}")
        outputs = renderer.render_to_png_fallback(src, full_png)

    # 2) Thumbnail
    thumb = Thumbnailer(size=thumb_size)
    thumb.make_thumbnail(full_png, thumb_png)

    return {
        "full_png_local": str(full_png),
        "thumb_png_local": str(thumb_png),
        "width": render_size[0],
        "height": render_size[1],
        "thumb_width": thumb_size[0],
        "thumb_height": thumb_size[1],
        "bounding_box": outputs.bounding_box
    }

# === Integration hook for part creation ======================================

def auto_thumbnail_on_part_create(
    model_path: str,
    part_id: str | int,
    supabase_url: str,
    supabase_key: str,
    order_process_no: Optional[str],
    on_success_update_db,  # callable(dict) -> None
    on_error_log=None,      # callable(str) -> None
) -> Optional[Dict]:
    """
    Call this function right after creating a part record (when you have its ID).
    Will render+thumbnail+upload and return dictionary with URLs.

    Args:
        model_path: Path to 3D file
        part_id: Part ID
        supabase_url: Supabase URL
        supabase_key: Supabase key
        order_process_no: Optional order number
        on_success_update_db: Callback to update DB with URLs
        on_error_log: Optional error logging callback

    Returns:
        Dictionary with results or None on error
    """
    try:
        out = generate_and_upload(
            model_path=model_path,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            part_id=part_id,
            order_process_no=order_process_no,
        )
        # Save to DB via callback:
        on_success_update_db(out)
        return out
    except Exception as e:
        if on_error_log:
            on_error_log(f"[render3d] Error for part {part_id}: {e}")
        return None


# === Standalone testing ======================================================

if __name__ == "__main__":
    import sys

    print("3D Render Module Test")
    print("=" * 60)

    if not OCC_AVAILABLE:
        print("ERROR: pythonocc-core is not installed!")
        print("Install with: conda install -c conda-forge pythonocc-core")
        sys.exit(1)

    # Test with command line argument or prompt
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        test_file = input("Enter path to STEP/IGES file (or press Enter to skip): ").strip()

    if test_file and os.path.exists(test_file):
        print(f"\nTesting with: {test_file}")

        try:
            # Test local rendering
            result = generate_local_only(test_file)

            print("\nSuccess! Generated files:")
            print(f"  Full PNG: {result['full_png_local']}")
            print(f"  Thumbnail: {result['thumb_png_local']}")

            if result.get('bounding_box'):
                bbox = result['bounding_box']
                print(f"\nBounding Box:")
                print(f"  Width: {bbox['width']:.2f} mm")
                print(f"  Height: {bbox['height']:.2f} mm")
                print(f"  Depth: {bbox['depth']:.2f} mm")

            # Try to open the generated image
            import subprocess
            try:
                if sys.platform == 'win32':
                    subprocess.run(['start', '', result['full_png_local']], shell=True)
                print("\nOpening generated image...")
            except:
                pass

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nNo test file provided or file not found.")
        print("Usage: python render3d.py [path_to_step_or_iges_file]")