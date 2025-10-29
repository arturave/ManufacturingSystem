# mfgviewer/sheet_thickness.py
from __future__ import annotations
import os, sys, statistics
from typing import Optional, Tuple, List

DEFAULT_FREECAD_BIN = r"C:\Program Files\FreeCAD 1.0\bin"

def ensure_freecad(bin_dir: str = DEFAULT_FREECAD_BIN) -> bool:
    """Dodaje FreeCAD do sys.path i œcie¿ek DLL (Windows)."""
    try:
        if os.name == "nt":
            if os.path.isdir(bin_dir):
                # od Python 3.8 wymagane do ³adowania DLL
                os.add_dll_directory(bin_dir)
            lib_dir = os.path.join(os.path.dirname(bin_dir), "lib")
            if os.path.isdir(lib_dir) and lib_dir not in sys.path:
                sys.path.append(lib_dir)
        # szybki test importu
        import FreeCAD as App  # noqa
        import Part            # noqa
        return True
    except Exception as e:
        print(f"[sheet_thickness] FreeCAD not ready: {e}")
        return False

def get_sheet_thickness_from_step(step_path: str,
                                  freecad_bin: str = DEFAULT_FREECAD_BIN
                                  ) -> Optional[Tuple[float, List[float]]]:
    """
    Wstêpne wykrywanie gruboœci blachy (WIP).
    Zwraca (dominanta, lista_próbek) albo None, jeœli brak FreeCAD/niepowodzenie.
    """
    if not os.path.isfile(step_path):
        return None
    if not ensure_freecad(freecad_bin):
        return None

    import FreeCAD as App
    import Part

    doc = App.newDocument("thk_tmp")
    shape = Part.Shape()
    try:
        shape.read(step_path)
    except Exception:
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass
        return None

    # TODO: Etap 2 – realny pomiar gruboœci (raycasty miêdzy równoleg³ymi œcianami)
    # Na razie zwróæ pust¹ próbkê (placeholder), ¿eby nie blokowaæ integracji GUI:
    samples: List[float] = []

    try:
        App.closeDocument(doc.Name)
    except Exception:
        pass

    if not samples:
        return None
    try:
        dominant = statistics.median_low(samples)
    except Exception:
        dominant = sum(samples)/len(samples)
    return dominant, samples
