import sys

sys.path.insert(
    0,
    r"C:\Users\rod63\OneDrive\Desktop\Combination Automotive  Diesel Mechanics Facility\CadQuery 2.6.1 source code\CadQuery-cadquery-aed5e55",
)
import cadquery as cq

print("cadquery file=" + getattr(cq, "__file__", "unknown"))
print("has_Workplane=" + str(hasattr(cq, "Workplane")))
print("symbols=" + ",".join([n for n in dir(cq) if not n.startswith("_")]))
