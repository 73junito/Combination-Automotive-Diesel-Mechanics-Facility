"""
Non-destructive DXF edit draft script.
Creates `facility_layout_draft.dxf` in outputs by:
 - adding FLOOR layer and copying polylines from STRUCTURAL_ANNOT
 - inserting title-block text on TITLE_BLOCK layer
 - adding sample dimension text (US units)
 - placing sample discipline labels on discipline layers

This script uses `ezdxf`. Install with:
  .\.venv\Scripts\python.exe -m pip install ezdxf

Run:
  .\.venv\Scripts\python.exe dxf_edit_draft.py

Note: This is a best-effort draft for review; coordinates are approximated.
"""

import sys
from pathlib import Path
from typing import Any

try:
    import ezdxf
    from ezdxf.entities import LWPolyline
except ImportError:
    print("ERROR: ezdxf is required. Install in venv:")
    print("  .\\.venv\\Scripts\\python.exe -m pip install ezdxf")
    raise

# Common set of exceptions that can arise when reading/parsing DXF entities.
# ezdxf exposes DXF-specific exceptions on some versions; include them
# when present to avoid referencing names that might not exist.
dxf_exceptions: tuple = (
    AttributeError,
    TypeError,
    ValueError,
    IndexError,
    UnicodeDecodeError,
)
if hasattr(ezdxf, "DXFStructureError"):
    dxf_exceptions = dxf_exceptions + (ezdxf.DXFStructureError,)
if hasattr(ezdxf, "DXFValueError"):
    dxf_exceptions = dxf_exceptions + (ezdxf.DXFValueError,)

ROOT = Path(__file__).resolve().parents[2]
INPUT_DXF = ROOT / "Python_Workflow" / "outputs" / "facility_layout_engineering.dxf"
OUT_DXF = ROOT / "Python_Workflow" / "outputs" / "facility_layout_draft.dxf"

if not INPUT_DXF.exists():
    print("Input DXF not found:", INPUT_DXF)
    sys.exit(2)

print("Loading", INPUT_DXF)
doc = ezdxf.readfile(str(INPUT_DXF))
ms: Any = doc.modelspace()


# Ensure layers exist
def ensure_layer(doc, name, color=7):
    if name not in doc.layers:
        doc.layers.new(name, dxfattribs={"color": color})


layers_to_ensure = [
    "FLOOR",
    "WALLS",
    "EQUIPMENT",
    "EQUIP_LABELS",
    "ELECTRICAL",
    "HVAC",
    "PLUMBING",
    "AIR_GAS",
    "AUTO_BAYS",
    "DIESEL_BAYS",
    "TEXT_LABELS",
    "TRAFFIC_FLOW",
    "DIMENSIONS",
    "TITLE_BLOCK",
]
for ly in layers_to_ensure:
    ensure_layer(doc, ly)

# Copy polylines/lines from STRUCTURAL_ANNOT -> FLOOR (non-destructive: duplicate)
copied = 0
for e in list(ms):
    try:
        layer = e.dxf.layer
    except (AttributeError, KeyError):
        layer = None
    if layer and layer.upper() == "STRUCTURAL_ANNOT":
        etype = e.dxftype()
        if etype == "LWPOLYLINE" or etype == "POLYLINE":
            points = []
            try:
                if isinstance(e, LWPolyline):
                    for v in e.get_points():
                        points.append((float(v[0]), float(v[1])))
                else:
                    # fallback: try vertices
                    for v in e.vertices():
                        vv = v  # type: Any
                        try:
                            points.append((float(vv.dxf.x), float(vv.dxf.y)))
                        except Exception:
                            try:
                                points.append((float(vv[0]), float(vv[1])))
                            except Exception:
                                pass
            except dxf_exceptions:
                # skip malformed/partial entities
                pass
            if points:
                ms.add_lwpolyline(points, dxfattribs={"layer": "FLOOR"})
                copied += 1
        elif etype == "LINE":
            try:
                start = (e.dxf.start[0], e.dxf.start[1])
                end = (e.dxf.end[0], e.dxf.end[1])
                ms.add_line(start, end, dxfattribs={"layer": "FLOOR"})
                copied += 1
            except (AttributeError, IndexError, TypeError, ValueError):
                # malformed line entity; ignore
                pass

print(f"Copied {copied} structural entities to FLOOR layer (draft).")

# Compute a rough bounding box from entity endpoints (for placing title block/dims)
minx = miny = float("inf")
maxx = maxy = float("-inf")
count_pts = 0
for e in ms:
    et = e.dxftype()
    try:
        if et == "LINE":
            sx, sy = e.dxf.start[0], e.dxf.start[1]
            ex, ey = e.dxf.end[0], e.dxf.end[1]
            for x, y in ((sx, sy), (ex, ey)):
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
                count_pts += 1
        elif et in ("LWPOLYLINE", "POLYLINE"):
            try:
                pts = []
                if isinstance(e, LWPolyline):
                    pts = [(float(p[0]), float(p[1])) for p in e.get_points()]
                else:
                    pts = []
                for x, y in pts:
                    minx = min(minx, x)
                    miny = min(miny, y)
                    maxx = max(maxx, x)
                    maxy = max(maxy, y)
                    count_pts += 1
            except dxf_exceptions:
                # skip malformed polyline
                pass
        elif et == "CIRCLE":
            cx, cy = e.dxf.center[0], e.dxf.center[1]
            r = e.dxf.radius
            for x, y in ((cx - r, cy - r), (cx + r, cy + r)):
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
                count_pts += 1
    except dxf_exceptions:
        # skip entities we can't interpret
        continue

if count_pts == 0:
    # fallback coordinates
    minx, miny, maxx, maxy = 0, 0, 2000, 1000

width = maxx - minx
height = maxy - miny
print("Approx bounds:", minx, miny, maxx, maxy)

# Title block insertion point: bottom-right corner offset
title_x = maxx + width * 0.03
title_y = miny - height * 0.08


# Add title block text entries on TITLE_BLOCK layer
def add_title_text(ms, text, pos, height=25):
    t = ms.add_text(text, dxfattribs={"layer": "TITLE_BLOCK", "height": height})
    try:
        t.dxf.insert = (float(pos[0]), float(pos[1]))
    except (AttributeError, TypeError, ValueError):
        # can't set insert point; leave default
        pass


add_title_text(
    ms,
    "Project: Combination Automotive & Diesel Facility",
    (title_x, title_y),
    height=24,
)
add_title_text(ms, "Author: Student Name", (title_x, title_y - 30), height=20)
add_title_text(ms, "Sheet: A1 - Facility Layout", (title_x, title_y - 55), height=20)
add_title_text(ms, "Date: 2026-01-26", (title_x, title_y - 80), height=18)
add_title_text(
    ms, "Revision: Rev 0 - Issued for Review", (title_x, title_y - 100), height=18
)
add_title_text(ms, 'Scale: 1/8" = 1\'-0"', (title_x, title_y - 125), height=18)

# Add a simple north arrow (triangle + text) on TEXT_LABELS
na_x = minx + width * 0.02
na_y = maxy + height * 0.04
# small triangle
ms.add_lwpolyline(
    [(na_x, na_y), (na_x - 10, na_y - 30), (na_x + 10, na_y - 30), (na_x, na_y)],
    dxfattribs={"layer": "TEXT_LABELS"},
)
t = ms.add_text("N", dxfattribs={"height": 20, "layer": "TEXT_LABELS"})
try:
    t.dxf.insert = (float(na_x - 6), float(na_y - 50))
except (AttributeError, TypeError, ValueError):
    pass

# Add sample dimension texts near midpoints
mid_x = minx + width * 0.5
mid_y = miny - height * 0.04
t = ms.add_text(
    "Overall width: 120'-0\"", dxfattribs={"layer": "DIMENSIONS", "height": 18}
)
try:
    t.dxf.insert = (float(mid_x - 60), float(mid_y))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Typical bay depth: 24'-0\"", dxfattribs={"layer": "DIMENSIONS", "height": 18}
)
try:
    t.dxf.insert = (float(mid_x - 60), float(mid_y - 30))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text("Main aisle: 12'-0\"", dxfattribs={"layer": "DIMENSIONS", "height": 18})
try:
    t.dxf.insert = (float(mid_x - 60), float(mid_y - 60))
except (AttributeError, TypeError, ValueError):
    pass

# Place discipline sample labels: find up to 3 entities in EQUIPMENT layer and place labels nearby
placed = 0
for e in ms:
    try:
        if e.dxf.layer.upper() == "EQUIPMENT" and placed < 6:
            # attempt to find a coords to place label
            x = y = None
            et = e.dxftype()
            try:
                if et == "CIRCLE":
                    x, y = e.dxf.center[0], e.dxf.center[1]
                elif et == "LINE":
                    x, y = (e.dxf.start[0] + e.dxf.end[0]) / 2, (
                        e.dxf.start[1] + e.dxf.end[1]
                    ) / 2
                elif et in ("LWPOLYLINE", "POLYLINE"):
                    try:
                        pts = list(e.get_points())
                        if pts:
                            x, y = pts[0][0], pts[0][1]
                    except dxf_exceptions:
                        pass
            except dxf_exceptions:
                # skip entities we can't inspect
                pass
            if x is None:
                continue
            label = "Two-post lift — 2,500 lb"
            t = ms.add_text(label, dxfattribs={"layer": "EQUIP_LABELS", "height": 14})
            try:
                t.dxf.insert = (float(x + 12), float(y + 6))
            except (AttributeError, TypeError, ValueError):
                pass
            placed += 1
    except (AttributeError, KeyError):
        # some entities may not have dxf attributes
        continue

# Discipline labels (global placements)
t = ms.add_text(
    "Panel LP-1 — 120/208V 3PH (East wall)",
    dxfattribs={"layer": "ELECTRICAL", "height": 14},
)
try:
    t.dxf.insert = (float(minx + 20), float(maxy - 30))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Diesel exhaust hood — 1,500 CFM", dxfattribs={"layer": "HVAC", "height": 14}
)
try:
    t.dxf.insert = (float(minx + 20), float(maxy - 60))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Floor drain → trench drain (slope w)",
    dxfattribs={"layer": "PLUMBING", "height": 14},
)
try:
    t.dxf.insert = (float(minx + 20), float(maxy - 90))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Compressed air drop @ each bay — 100 PSI",
    dxfattribs={"layer": "AIR_GAS", "height": 14},
)
try:
    t.dxf.insert = (float(minx + 20), float(maxy - 120))
except (AttributeError, TypeError, ValueError):
    pass

# Legend update: add a short legend near title block on TITLE_BLOCK layer
lg_y = title_y - 160
t = ms.add_text("Legend:", dxfattribs={"layer": "TITLE_BLOCK", "height": 16})
try:
    t.dxf.insert = (float(title_x), float(lg_y))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Exhaust Hood — HVAC (HVAC)", dxfattribs={"layer": "TITLE_BLOCK", "height": 12}
)
try:
    t.dxf.insert = (float(title_x), float(lg_y - 22))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Floor Drain — Plumbing (PLUMBING)",
    dxfattribs={"layer": "TITLE_BLOCK", "height": 12},
)
try:
    t.dxf.insert = (float(title_x), float(lg_y - 40))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Air Drop — Air/Gas (AIR_GAS)", dxfattribs={"layer": "TITLE_BLOCK", "height": 12}
)
try:
    t.dxf.insert = (float(title_x), float(lg_y - 58))
except (AttributeError, TypeError, ValueError):
    pass
t = ms.add_text(
    "Lift — Equipment (EQUIPMENT)", dxfattribs={"layer": "TITLE_BLOCK", "height": 12}
)
try:
    t.dxf.insert = (float(title_x), float(lg_y - 76))
except (AttributeError, TypeError, ValueError):
    pass

# Save draft
print("Writing draft to", OUT_DXF)
doc.saveas(str(OUT_DXF))
print("Draft written:", OUT_DXF)
