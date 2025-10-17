# 3D CAD File Rendering Setup Guide
## ManufacturingSystem - STEP/IGES Support

## Overview
This guide covers the setup and usage of 3D CAD file rendering functionality in the ManufacturingSystem application. The system supports STEP (.stp, .step) and IGES (.igs, .iges) file formats.

## Features
- ✅ Render STEP/IGES files to PNG images
- ✅ Generate isometric view projections
- ✅ Create high-resolution and thumbnail versions
- ✅ Extract bounding box dimensions
- ✅ Fallback placeholder generation when libraries unavailable
- ✅ Optional Supabase storage integration

## Architecture
```
render3d.py (New Module)
    ├── StepIgesRenderer - 3D rendering engine
    ├── Thumbnailer - Thumbnail generation
    └── SupabaseUploader - Cloud storage (optional)
         ↓
cad_processing.py (Updated)
    ├── process_step_to_image() - Uses render3d
    └── process_iges_to_image() - Uses render3d
         ↓
part_edit_enhanced.py (UI Integration)
    └── process_cad_file() - Handles all CAD files
```

## Installation Requirements

### 1. Basic Requirements (Already Installed)
```bash
pip install pillow
pip install customtkinter
pip install ezdxf
pip install pymupdf
```

### 2. 3D Rendering Requirements

#### Option A: Using Conda (Recommended)
```bash
# Install Anaconda or Miniconda first
# Download from: https://www.anaconda.com/products/individual

# Then install pythonocc-core
conda install -c conda-forge pythonocc-core

# Or for Windows specifically:
conda install -c dlr-sc pythonocc-core
```

#### Option B: Using pip (Limited Support)
```bash
# Note: pip installation is more complex and may not work on all systems
pip install pythonocc-core

# If above fails, you may need to install dependencies manually:
pip install oce
pip install svgwrite
```

### 3. Optional: Supabase Integration
```bash
pip install supabase
```

## Testing the Installation

### 1. Check Module Availability
```python
python -c "from OCC.Core.STEPControl import STEPControl_Reader; print('pythonocc-core OK')"
```

### 2. Run Test Scripts
```bash
# Test 3D rendering
python test_3d_rendering.py

# Test CAD processing (includes 3D)
python test_cad_auto.py
```

## Usage Examples

### 1. Direct 3D Rendering (Standalone)
```python
from render3d import generate_local_only

# Render STEP/IGES file to PNG
result = generate_local_only(
    model_path="part.stp",
    render_size=(1200, 900),
    thumb_size=(300, 225)
)

print(f"Full image: {result['full_png_local']}")
print(f"Thumbnail: {result['thumb_png_local']}")
print(f"Bounding box: {result['bounding_box']}")
```

### 2. Integration with CADProcessor
```python
from cad_processing import CADProcessor

# Process any CAD file (DXF/DWG/STEP/IGES)
high_success, low_success = CADProcessor.process_cad_file_both_resolutions(
    "model.stp",
    "output_high.png",
    "output_low.png"
)
```

### 3. With Supabase Upload
```python
from render3d import generate_and_upload

# Render and upload to Supabase
result = generate_and_upload(
    model_path="part.iges",
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY,
    part_id="PART-123",
    order_process_no="2025-00001"
)

print(f"Cloud URL: {result['full_png_url']}")
```

## Fallback Behavior

If `pythonocc-core` is not installed, the system will:
1. First try the new `render3d` module with full 3D rendering
2. If that fails, use `render3d.render_to_png_fallback()` for info image
3. If render3d is unavailable, create a simple placeholder image

The fallback images include:
- File name and type
- File size
- Bounding box dimensions (if extractable)
- Clear message that 3D preview is unavailable

## Troubleshooting

### Problem: "pythonocc-core not installed" error
**Solution:** Install using conda as shown above. pip installation may not work on all systems.

### Problem: "Display not found" on Linux servers
**Solution:** Use virtual display for headless rendering:
```bash
# Install xvfb
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a python your_script.py
```

### Problem: ImportError with OCC modules
**Solution:** Ensure conda environment is activated:
```bash
conda activate your_env_name
```

### Problem: Qt platform plugin error
**Solution:** Install Qt dependencies:
```bash
conda install pyqt
# or
pip install PyQt5
```

## File Support Matrix

| Format | Extension | 2D/3D | Library Required | Fallback Available |
|--------|-----------|-------|------------------|-------------------|
| DXF    | .dxf      | 2D    | ezdxf            | ✅ matplotlib     |
| DWG    | .dwg      | 2D    | ezdxf + ODA      | ✅ matplotlib     |
| STEP   | .stp/.step| 3D    | pythonocc-core   | ✅ placeholder    |
| IGES   | .igs/.iges| 3D    | pythonocc-core   | ✅ placeholder    |

## Performance Considerations

1. **3D Rendering Speed**: First render may be slow (5-10 seconds) due to library initialization
2. **Memory Usage**: Large 3D models may require significant RAM (>1GB)
3. **Caching**: Use `.cache_renders/` directory for repeated renders
4. **Resolution**: Default 1200x900 for full, 360x270 for thumbnails

## Integration with Part Management

The system automatically:
1. Detects CAD file type (DXF/DWG vs STEP/IGES)
2. Chooses appropriate rendering method
3. Generates both high-res and low-res versions
4. Stores paths in database
5. Displays preview in UI

## API Reference

### render3d.py Functions

#### `generate_local_only(model_path, output_dir=None, render_size=(1200,900), thumb_size=(360,270))`
Generate PNG and thumbnail locally without upload.

#### `generate_and_upload(model_path, supabase_url, supabase_key, part_id, ...)`
Generate and upload to Supabase storage.

#### `StepIgesRenderer.render_to_png(src, out_png, headless=False)`
Core rendering function with optional headless mode.

#### `StepIgesRenderer.render_to_png_fallback(src, out_png)`
Fallback that creates info image when rendering fails.

### CADProcessor Updates

#### `process_step_to_image(step_path, output_path, image_size)`
Now uses render3d module with automatic fallback.

#### `process_iges_to_image(iges_path, output_path, image_size)`
Now uses render3d module with automatic fallback.

## Future Enhancements

1. **Additional Formats**: Support for STL, OBJ, FBX
2. **Multiple Views**: Generate front/side/top views
3. **Animation**: Rotating 3D preview GIFs
4. **Measurement Tools**: Interactive dimension extraction
5. **Assembly Support**: Handle multi-part STEP files
6. **Web Viewer**: Three.js based browser preview

## Support

For issues or questions:
1. Check test scripts: `test_3d_rendering.py`, `test_cad_auto.py`
2. Review error messages in console output
3. Ensure all dependencies are properly installed
4. Try fallback mode if full rendering fails

## License

This module uses:
- **pythonocc-core**: LGPL v3 license
- **OpenCASCADE**: LGPL v2.1 license
- **Pillow**: HPND license

Ensure compliance with these licenses in your deployment.