import os
from typing import Any, Optional

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[Any] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF = os.path.join(OUT, "facility_layout_colored.dxf")

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
        if e.dxf.layer != "EQUIP_LABELS":
            continue
    except AttributeError:
        continue
    et = e.dxftype()
    if et == "TEXT":
        text = e.dxf.text
        color = getattr(e.dxf, "color", None)
        rows.append((text, color))
    elif et == "MTEXT":
        text = e.text
        color = getattr(e.dxf, "color", None)
        rows.append((text, color))

print("Found", len(rows), "labels on EQUIP_LABELS")
for t, c in rows:
    print(repr(t), "-> color", c)
