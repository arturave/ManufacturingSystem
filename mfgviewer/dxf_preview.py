"""
2D preview DXF/DWG dla ManufacturingSystem:
- DXF: czytany bezpośrednio (ezdxf)
- DWG: auto-konwersja do DXF przez ODAFileConverter (ezdxf.addons.odafc)
- Poprawna obsługa: LINE, CIRCLE, ARC, (LW)POLYLINE z bulgami (virtual_entities),
  SPLINE (flattening), ELLIPSE (ConstructionEllipse)
- Matplotlib (QtAgg) + gabaryty X×Y

Nie wymaga 'ezdxf.curves'.
"""

from __future__ import annotations
from pathlib import Path
import math, os, tempfile, shutil
from typing import Iterable, Optional, List, Tuple

import ezdxf
from ezdxf.addons import odafc
from ezdxf.math import ConstructionEllipse

# --- konfiguracja ODA (podajemy domyślną ścieżkę z Twojej instalacji) ---
DEFAULT_ODA = r"C:\Program Files\ODA\ODAFileConverter 26.4.0\ODAFileConverter.exe"
if os.path.exists(DEFAULT_ODA):
    try:
        ezdxf.options.set("odafc-addon", "win_exec_path", DEFAULT_ODA)
    except Exception:
        pass

# --- Qt + Matplotlib ---
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets, QtCore

SUPPORTED_2D = (".dxf", ".dwg")

# ---------------- pomocnicze: sampling krzywych ----------------

def _circle_pts(cx: float, cy: float, r: float, seg: int = 96) -> List[Tuple[float, float]]:
    pts = []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts

def _arc_pts(cx: float, cy: float, r: float, a0_deg: float, a1_deg: float) -> List[Tuple[float, float]]:
    a0 = math.radians(a0_deg); a1 = math.radians(a1_deg)
    if a1 < a0:
        a1 += 2.0 * math.pi
    span = a1 - a0
    seg = max(16, int(96 * span / (2.0 * math.pi)))
    pts = []
    for i in range(seg + 1):
        a = a0 + span * i / seg
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def _ellipse_pts(ell: ConstructionEllipse, max_seg=128) -> List[Tuple[float, float]]:
    span = abs(ell.t1 - ell.t0)
    seg = max(32, min(max_seg, int(96 * span / (2.0 * math.pi))))
    out = []
    for i in range(seg + 1):
        t = ell.t0 + (ell.t1 - ell.t0) * i / seg
        x, y, *_ = ell.point(t)
        out.append((x, y))
    return out

def _spline_pts(entity, max_err=0.25) -> List[Tuple[float, float]]:
    tool = entity.construction_tool()
    if tool is None:
        return []
    pts = tool.flattening(distance=max_err)  # list[(x,y[,z])]
    return [(p[0], p[1]) for p in pts]

def _polyline_virtual(entity):
    """Zwróć wirtualne encje (LINE/ARC) dla (LW)POLYLINE (z bulgami)."""
    try:
        yield from entity.virtual_entities()
    except Exception:
        # fallback: gołe wierzchołki jako linie
        verts = getattr(entity, "vertices", [])
        if not verts:
            return
        def _pt(v):
            if hasattr(v, "dxf"):
                p = v.dxf.location; return (p.x, p.y)
            return (v[0], v[1])
        pts = [_pt(v) for v in verts]
        for i in range(len(pts) - 1):
            yield _SimpleLine(pts[i], pts[i+1])

class _SimpleLine:
    def __init__(self, p1, p2): self._p1, self._p2 = p1, p2
    def dxftype(self): return "LINE"
    class _D:
        def __init__(self, p1, p2):
            class V: 
                def __init__(self, p): self.x, self.y = p
            self.start, self.end = V(p1), V(p2)
    @property
    def dxf(self): return self._D(self._p1, self._p2)

# ---------------- parsowanie DXF/DWG ----------------

def _open_any_2d(path: Path):
    p = Path(path); ext = p.suffix.lower()
    if ext == ".dxf":
        doc = ezdxf.readfile(str(p))
        return doc, doc.modelspace(), False, p
    if ext == ".dwg":
        if not odafc.is_installed():
            raise RuntimeError("Brak ODA File Converter – nie mogę otworzyć DWG.")
        tmp = Path(tempfile.mkdtemp(prefix="dwg2dxf_"))
        out = tmp / (p.stem + ".dxf")
        odafc.convert(str(p), str(out), version="R2018", audit=True, recursive=False)
        doc = ezdxf.readfile(str(out))
        return doc, doc.modelspace(), True, out
    raise ValueError("Obsługiwane 2D: .dxf / .dwg")

def _extract_polys(msp, only_layers: Optional[Iterable[str]] = None) -> List[List[Tuple[float, float]]]:
    res: List[List[Tuple[float, float]]] = []
    def add(poly):
        if len(poly) >= 2: res.append(poly)

    for e in msp:
        try:
            if only_layers and e.dxf.layer not in only_layers:
                continue
            t = e.dxftype()
            if t == "LINE":
                s, ee = e.dxf.start, e.dxf.end
                add([(s.x, s.y), (ee.x, ee.y)])

            elif t in ("LWPOLYLINE", "POLYLINE"):
                for ve in _polyline_virtual(e):
                    if ve.dxftype() == "LINE":
                        s, ee = ve.dxf.start, ve.dxf.end
                        add([(s.x, s.y), (ee.x, ee.y)])
                    elif ve.dxftype() == "ARC":
                        c, r = ve.dxf.center, ve.dxf.radius
                        add(_arc_pts(c.x, c.y, r, ve.dxf.start_angle, ve.dxf.end_angle))

            elif t == "CIRCLE":
                c, r = e.dxf.center, e.dxf.radius
                add(_circle_pts(c.x, c.y, r))

            elif t == "ARC":
                c, r = e.dxf.center, e.dxf.radius
                add(_arc_pts(c.x, c.y, r, e.dxf.start_angle, e.dxf.end_angle))

            elif t == "SPLINE":
                add(_spline_pts(e))

            elif t == "ELLIPSE":
                tool = e.construction_tool()
                if tool is None:
                    # w rzadkich wypadkach brak toola – przelicz ręcznie
                    center = (e.dxf.center.x, e.dxf.center.y)
                    maj = (e.dxf.major_axis.x, e.dxf.major_axis.y)
                    ell = ConstructionEllipse.from_parametrization(
                        center=center, major_axis=maj, ratio=e.dxf.ratio,
                        start_param=e.dxf.start_param, end_param=e.dxf.end_param
                    )
                else:
                    ell = tool
                add(_ellipse_pts(ell))
            # HATCH/REGION/MLINE – pomin. (do rozbudowy)
        except Exception:
            continue
    return res

def preview_file_2d(path: Path, ax, layers: Optional[Iterable[str]] = None, show_bbox=True) -> Tuple[float, float]:
    doc, msp, was_tmp, dxf_path = _open_any_2d(Path(path))
    try:
        polys = _extract_polys(msp, layers)
        if not polys:
            ax.text(0.5, 0.5, "Brak geometrii", ha="center", va="center", color="w", transform=ax.transAxes)
            ax.set_axis_off(); return (0.0, 0.0)

        xs, ys = [], []
        for poly in polys:
            px, py = zip(*poly)
            xs.extend(px); ys.extend(py)
            ax.plot(px, py, linewidth=1.2, color="#E6E6E6", solid_capstyle="round")

        minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
        w, h = (maxx - minx), (maxy - miny)
        pad = 0.02 * max(w, h)
        ax.set_xlim(minx - pad, maxx + pad); ax.set_ylim(miny - pad, maxy + pad)
        ax.set_aspect("equal", adjustable="box")
        ax.set_facecolor("#0E0F12")
        ax.grid(True, color="#2a2d31", alpha=0.35, linewidth=0.6)
        ax.tick_params(colors="#7d8596")

        if show_bbox:
            ax.text(0.99, 0.98, f"{w:.3f} × {h:.3f}", color="#61a6ff", ha="right", va="top",
                    fontsize=11, transform=ax.transAxes)
        return float(w), float(h)
    finally:
        if was_tmp:
            try:
                tmp_root = Path(dxf_path).parent
                for p in tmp_root.glob("*"):
                    try: p.unlink()
                    except: pass
                tmp_root.rmdir()
            except Exception:
                pass

# ---------------- Qt widget do integracji z app.py ----------------

class DxfCanvas(QtWidgets.QWidget):
    """Prosty widget: matplotlib canvas + API load_path()."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(9, 5.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.canvas)

        self._bg = "black"
        self._layers: Optional[List[str]] = None

    def set_background(self, name: str = "black"):
        self._bg = name
        self.ax.set_facecolor("#0E0F12" if name == "black" else "white")
        self.canvas.draw_idle()

    def set_layers(self, layers: Optional[Iterable[str]]):
        self._layers = list(layers) if layers else None

    def set_tolerance(self, tol: float):
        # placeholder – jeżeli chcesz sterować dokładnością flatteningu SPLINE
        pass

    def clear(self):
        self.ax.clear()
        self.canvas.draw_idle()

    def load_path(self, path: str | Path):
        self.ax.clear()
        try:
            preview_file_2d(Path(path), self.ax, layers=self._layers, show_bbox=True)
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Błąd podglądu:\n{e}", ha="center", va="center", color="r", transform=self.ax.transAxes)
        self.fig.tight_layout()
        self.canvas.draw_idle()

# --------------- uruchomienie samodzielne ---------------

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = DxfCanvas()
    w.resize(1100, 650)
    w.set_background("black")
    if len(sys.argv) > 1:
        w.load_path(sys.argv[1])
    w.show()
    sys.exit(app.exec())

