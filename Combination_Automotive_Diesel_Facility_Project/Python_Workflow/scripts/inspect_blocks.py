import os
from types import ModuleType
from typing import Any, Optional

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[ModuleType] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF = os.path.join(OUT, "facility_layout_blocks.dxf")
if ezdxf is None:
    print("ezdxf not available")
    raise SystemExit(1)
if not os.path.exists(DXF):
    print("DXF not found:", DXF)
    raise SystemExit(2)
doc = ezdxf.readfile(DXF)
msp = doc.modelspace()
rows = []
for e in msp:
    try:
        layer = e.dxf.layer
    except AttributeError:
        continue
    if layer != "EQUIP_LABELS":
        continue
    t = e.dxftype()
    if t == "INSERT":
        name = e.dxf.name
        ins = tuple(e.dxf.insert)
        color = getattr(e.dxf, "color", None)
        rows.append((name, ins, color))
print("Found", len(rows), "INSERTs on EQUIP_LABELS")
for r in rows:
    print(r)
