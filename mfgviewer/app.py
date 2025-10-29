import os
from PySide6 import QtWidgets, QtGui
from .backend_vtk import VtkViewerWidget, SUPPORTED_3D
from .dxf_preview import DxfCanvas, SUPPORTED_2D

ALL_FILTER = "All supported (*.stl *.step *.stp *.iges *.igs *.dxf *.dwg);;3D (*.stl *.step *.stp *.iges *.igs);;2D (*.dxf *.dwg)"

class PreviewWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ManufacturingSystem – 2D/3D Preview")
        self.resize(1200, 800)

        self.stack = QtWidgets.QStackedWidget()
        self.vtk = VtkViewerWidget()
        self.dxf = DxfCanvas()
        self.stack.addWidget(self.vtk)
        self.stack.addWidget(self.dxf)
        self.setCentralWidget(self.stack)

        self._build_toolbar()
        self.statusBar().showMessage("Ready")

    def _build_toolbar(self):
        tb = self.addToolBar("Main")

        openAct = QtGui.QAction("Open…", self); openAct.triggered.connect(self.on_open)
        tb.addAction(openAct)

        self.modeCombo = QtWidgets.QComboBox()
        self.modeCombo.addItems(["realistic", "realistic-edges", "wireframe"])
        self.modeCombo.currentTextChanged.connect(lambda m: self.vtk.set_shading(m))
        tb.addSeparator(); tb.addWidget(QtWidgets.QLabel("3D shading: ")); tb.addWidget(self.modeCombo)

        snapAct = QtGui.QAction("Snapshot", self); snapAct.triggered.connect(self.on_snapshot)
        tb.addSeparator(); tb.addAction(snapAct)

        bgAct = QtGui.QAction("2D: Toggle dark", self); bgAct.triggered.connect(self.toggle_2d_bg)
        tb.addAction(bgAct)

    def toggle_2d_bg(self):
        curr = "black" if self.dxf._bg != "black" else "white"
        self.dxf.set_background(curr)

    def on_open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", "", ALL_FILTER)
        if not path:
            return
        self.open_any(path)

    def open_any(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext in SUPPORTED_3D:
            self.stack.setCurrentWidget(self.vtk)
            self.vtk.load_path(path)
            self.statusBar().showMessage(f"Loaded 3D: {os.path.basename(path)}")
        elif ext in SUPPORTED_2D:
            self.stack.setCurrentWidget(self.dxf)
            self.dxf.load_path(path)
            self.statusBar().showMessage(f"Loaded 2D: {os.path.basename(path)}")
        else:
            QtWidgets.QMessageBox.warning(self, "Unsupported", f"Unsupported file: {ext}")

    def on_snapshot(self):
        w = self.stack.currentWidget()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save PNG", "", "PNG (*.png)")
        if not path:
            return
        if w is self.vtk:
            self.vtk.snapshot_png(path)
        else:
            self.dxf.save_png(path, dpi=220)
        self.statusBar().showMessage(f"Saved: {os.path.basename(path)}")

def main():
    app = QtWidgets.QApplication([])
    win = PreviewWindow()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
