from pathlib import Path
import os
import ezdxf
from ezdxf.addons import odafc

ODA_EXE = r"C:\Program Files\ODA\ODAFileConverter 26.4.0\ODAFileConverter.exe"
if os.path.exists(ODA_EXE):
    try:
        ezdxf.options.set('odafc-addon', 'win_exec_path', ODA_EXE)
    except Exception:
        pass

print("Manual check ODA exists:", os.path.exists(ODA_EXE))
print("odafc.is_installed():   ", odafc.is_installed())

# szybki smoke-test DWG -> DXF (jeśli masz .dwg obok)
sample_dwg = Path(r"C:\temp\sample.dwg")
if sample_dwg.exists():
    out = Path(r"C:\temp\_odafc_test_out.dxf")
    odafc.convert(str(sample_dwg), str(out), version="R2018", audit=True, recursive=False)
    print("Converted to:", out, "exists?", out.exists())

# szybki test DXF 2D
sample_dxf = Path(r"C:\temp\12-019145_0,5mm_INOX_65szt.dxf")
if sample_dxf.exists():
    from mfgviewer.dxf_preview import preview_window
    preview_window(sample_dxf)
else:
    print("Brak pliku DXF do testu:", sample_dxf)

