from PySide6 import QtWidgets, QtCore
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor, vtkPolyDataMapper, vtkProperty
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals, vtkTriangleFilter
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

import os, tempfile

try:
    import cadquery as cq
    _HAS_CQ = True
except Exception:
    _HAS_CQ = False

SUPPORTED_3D = (".stl", ".step", ".stp", ".iges", ".igs")

def convert_to_stl(src_path: str) -> str:
    ext = os.path.splitext(src_path)[1].lower()
    if ext == ".stl":
        return src_path
    if not _HAS_CQ:
        raise RuntimeError("CadQuery not available. Install cadquery to auto-convert STEP/IGES to STL.")
    if ext in (".step", ".stp"):
        shape = cq.importers.importStep(src_path)
    elif ext in (".iges", ".igs"):
        shape = cq.importers.importers.importIGES(src_path)
    else:
        raise RuntimeError(f"Unsupported extension for conversion: {ext}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
    tmp.close()
    cq.exporters.export(shape, tmp.name)
    return tmp.name

class VtkViewerWidget(QtWidgets.QWidget):
    fileLoaded = QtCore.Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.layout().addWidget(self.vtk_widget)

        self.renderer = vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.iren.SetInteractorStyle(vtkInteractorStyleTrackballCamera())
        self.iren.Initialize()

        self.model_actor = None
        self.colors = vtkNamedColors()
        self.set_background("SlateGray")

    def set_background(self, name="SlateGray"):
        self.renderer.SetBackground(self.colors.GetColor3d(name))

    def load_path(self, path: str):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_3D:
            raise RuntimeError(f"Unsupported 3D file: {ext}  (supported: {SUPPORTED_3D})")
        stl_path = convert_to_stl(path) if ext != ".stl" else path

        if self.model_actor:
            self.renderer.RemoveActor(self.model_actor)
            self.model_actor = None

        reader = vtkSTLReader()
        reader.SetFileName(stl_path)
        reader.Update()

        tri = vtkTriangleFilter()
        tri.SetInputConnection(reader.GetOutputPort())
        tri.Update()

        norms = vtkPolyDataNormals()
        norms.SetInputConnection(tri.GetOutputPort())
        norms.SetSplitting(True); norms.SetFeatureAngle(30.0)
        norms.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(norms.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(self.colors.GetColor3d("LightSteelBlue"))
        actor.GetProperty().SetInterpolationToPhong()

        self.model_actor = actor
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        self.fileLoaded.emit(path)

    def set_shading(self, mode: str = "realistic"):
        if not self.model_actor:
            return
        prop = self.model_actor.GetProperty()
        mode = (mode or "").lower()
        if mode == "wireframe":
            prop.SetRepresentationToWireframe()
            prop.EdgeVisibilityOff()
        elif mode == "realistic-edges":
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOn()
            prop.SetEdgeColor(0.2, 0.2, 0.2)
        else:
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOff()
        self.vtk_widget.GetRenderWindow().Render()

    def snapshot_png(self, out_path: str):
        from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
        from vtkmodules.vtkIOImage import vtkPNGWriter

        w2i = vtkWindowToImageFilter()
        w2i.SetInput(self.vtk_widget.GetRenderWindow())
        w2i.Update()
        writer = vtkPNGWriter()
        writer.SetFileName(out_path)
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
