import sys
import FreeCAD as App
import Part

print("Starting STEP file test")

# Get file from argument
if len(sys.argv) > 1:
    step_file = sys.argv[1]
    print(f"Loading: {step_file}")

    doc = App.newDocument("TestDoc")

    try:
        Part.insert(step_file, doc.Name)
        print("File loaded successfully")

        shapes = []
        for obj in doc.Objects:
            if hasattr(obj, 'Shape'):
                shapes.append(obj.Shape)
                print(f"Found shape: {obj.Name}")

        if shapes:
            compound = Part.makeCompound(shapes)
            bbox = compound.BoundBox
            print(f"Width: {bbox.XLength:.2f} mm")
            print(f"Height: {bbox.YLength:.2f} mm")
            print(f"Depth: {bbox.ZLength:.2f} mm")
            print(f"Volume: {compound.Volume:.2f} mm3")
        else:
            print("No shapes found")

    except Exception as e:
        print(f"Error: {e}")

    App.closeDocument(doc.Name)

else:
    print("No file provided")

print("Test completed")
sys.exit(0)