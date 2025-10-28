# Simple test
print("Hello from FreeCAD")
import sys
print(f"Python version: {sys.version}")
try:
    import FreeCAD
    print(f"FreeCAD version: {FreeCAD.Version()}")
except:
    print("Cannot import FreeCAD")