# mfgviewer — 2D/3D preview for ManufacturingSystem

Features:
- **3D**: STL natively; STEP/IGES via optional **CadQuery** conversion (Apache-2.0)
- **2D**: DXF preview using **ezdxf** + **matplotlib** embedded in Qt
- **UI**: PySide6 (Qt) + VTK (for 3D) / Matplotlib (for 2D)

## Install (Windows / Visual Studio Python)
```powershell
pip install vtk==9.5.2 PySide6 ezdxf matplotlib
# optional for STEP/IGES -> STL conversion:
pip install cadquery
```
> If you cannot install CadQuery, convert STEP/IGES to STL outside and open STL.

## Run standalone
```powershell
python -m mfgviewer.app
```

## Integrate in VS External Tools
Command:
```
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
```
Args:
```
-ExecutionPolicy Bypass -NoProfile -Command "python -m mfgviewer.app"
```
