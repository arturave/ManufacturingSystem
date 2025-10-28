# FreeCAD 3D Rendering Setup Guide

## Overview

This manufacturing system now uses **FreeCAD** for rendering 3D CAD files (STEP/IGES) instead of OpenCASCADE (pythonocc-core). FreeCAD provides a more reliable and feature-rich solution for processing 3D CAD files.

## System Architecture

```
[User uploads STEP/IGES file]
           ↓
[part_edit_enhanced.py - UI]
           ↓
[cad_processing.py - Router]
           ↓
[freecad_renderer.py - FreeCAD Integration]
           ↓
[FreeCADCmd.exe - Headless Processing]
           ↓
[PNG Image Output + Geometry Data]
```

## Installation

### 1. Install FreeCAD

1. Download FreeCAD 0.21 or newer from: https://www.freecad.org/downloads.php
2. Install using the Windows installer
3. Default installation path: `C:\Program Files\FreeCAD 0.21\`

### 2. Configure Environment

Edit the `.env` file in the project root and update the FreeCAD path:

```env
FREECAD_CMD=C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe
```

Common FreeCAD installation paths:
- `C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe`
- `C:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe`
- `C:\Program Files (x86)\FreeCAD 0.21\bin\FreeCADCmd.exe`

### 3. Install Python Dependencies

```bash
pip install python-dotenv pillow
```

## Testing

### Quick Test

Run the test script to verify the installation:

```bash
python test_freecad_rendering.py
```

### Test with a CAD File

```bash
python test_freecad_rendering.py path/to/your/file.step
```

This will:
1. Check if FreeCAD is installed correctly
2. Render the 3D file to PNG
3. Extract geometry information (dimensions, volume, etc.)
4. Generate high-res and low-res versions

## How It Works

### 1. FreeCAD Renderer (`freecad_renderer.py`)

The `FreeCADRenderer` class provides:
- **render_to_png()**: Renders STEP/IGES to PNG image
- **render_with_info_fallback()**: Tries rendering, falls back to info image if fails
- **extract_geometry_info()**: Extracts bounding box, volume, and other metrics

### 2. Processing Flow

When a user uploads a 3D file:

1. **File Upload**: User selects STEP/IGES file in the UI
2. **Processing**: `CADProcessor.process_cad_file()` is called
3. **FreeCAD Priority**: System first tries FreeCAD rendering
4. **Fallback**: If FreeCAD fails, tries render3d module (if OCC available)
5. **Last Resort**: Creates placeholder image with file information

### 3. Generated Outputs

For each 3D file, the system generates:
- **High-resolution image** (1920x1080) for detailed preview
- **Low-resolution thumbnail** (200x200) for quick display
- **Geometry information** (dimensions, volume, surface area)

## File Modifications

### Modified Files

1. **cad_processing.py**:
   - Added FreeCAD as primary renderer for STEP/IGES
   - Maintains backward compatibility with OCC

2. **New Files**:
   - `freecad_renderer.py` - FreeCAD integration module
   - `.env` - Environment configuration
   - `test_freecad_rendering.py` - Test suite
   - `FREECAD_SETUP.md` - This documentation

## Advantages of FreeCAD

1. **No Complex Dependencies**: Unlike pythonocc-core, FreeCAD is a simple installer
2. **Better Compatibility**: Works with more CAD file variations
3. **Geometry Extraction**: Can extract detailed geometry information
4. **Reliable Rendering**: More stable rendering pipeline
5. **Future Extensions**: Can be extended for sheet metal unfolding (as in your reference)

## Troubleshooting

### FreeCAD Not Found

**Error**: `FreeCADCmd.exe not found`

**Solution**:
1. Verify FreeCAD is installed
2. Update `.env` file with correct path
3. Check path exists: `dir "C:\Program Files\FreeCAD 0.21\bin\"`

### Rendering Fails

**Error**: `Rendering failed, using fallback`

**Possible Causes**:
1. Corrupted CAD file
2. Unsupported geometry in file
3. FreeCAD missing required workbenches

**Solution**:
1. Test with a known good STEP/IGES file
2. Check FreeCAD can open the file manually
3. Update FreeCAD to latest version

### Module Import Errors

**Error**: `ImportError: No module named freecad_renderer`

**Solution**:
1. Ensure `freecad_renderer.py` is in the project directory
2. Check Python path includes the project directory

## Future Enhancements

Based on your sheet metal unfold reference, future capabilities could include:

1. **Sheet Metal Processing**:
   - Install SheetMetal workbench in FreeCAD
   - Add unfolding capabilities
   - Generate DXF flat patterns

2. **Advanced Geometry Analysis**:
   - Material thickness detection
   - Bend detection and counting
   - Manufacturing feasibility checks

3. **Batch Processing**:
   - Process multiple files at once
   - Parallel rendering for performance

## Support

For issues or questions:
1. Check test output: `python test_freecad_rendering.py`
2. Verify FreeCAD installation
3. Review error logs in console output

## Version Information

- **System Version**: 1.0
- **FreeCAD Version**: 0.21+ recommended
- **Python Version**: 3.11+ compatible
- **Platform**: Windows 10/11

---

*Generated for ManufacturingSystem - FreeCAD Integration*