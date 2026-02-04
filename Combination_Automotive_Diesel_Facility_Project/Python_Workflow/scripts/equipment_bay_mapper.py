"""
Map equipment items from equipment CSVs to DXF bay locations.
- Reads `facility_layout_sample.dxf`
- Extracts bay LWPolylines from layers `AUTO_BAYS` and `DIESEL_BAYS`
- Loads `essential_equipment.csv` and `nonessential_equipment.csv`
- Expands each item by its `Quantity` into individual units and assigns sequentially to bays (left-to-right)
- Writes `equipment_bay_mapping.csv` and `equipment_bay_mapping.xlsx` to outputs
"""

import csv
import os
from collections import namedtuple
from typing import Any, Optional

import pandas as pd

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[Any] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_PATH = os.path.join(OUT, "facility_layout_sample.dxf")
ESS_CSV = os.path.join(OUT, "essential_equipment.csv")
NON_CSV = os.path.join(OUT, "nonessential_equipment.csv")

Bay = namedtuple("Bay", ["layer", "name", "minx", "miny", "maxx", "maxy", "cx", "cy"])


def bbox_from_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def collect_bays():
    if ezdxf is None:
        raise RuntimeError("ezdxf not installed")
    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    bays = []
    for e in msp:
        # check lightweight polylines (LWPOLYLINE) and polyline types
        etype = e.dxftype()
        layer = getattr(e.dxf, "layer", "")
        if etype in ("LWPOLYLINE", "POLYLINE") and layer in (
            "AUTO_BAYS",
            "DIESEL_BAYS",
        ):
            # get points (works for lwpolyline and polyline)
            try:
                pts = (
                    list(e.get_points())
                    if hasattr(e, "get_points")
                    else list(e.points())
                )
            except AttributeError:
                # fallback: try to read vertices
                pts = [tuple(v) for v in e.vertices()]
            minx, miny, maxx, maxy = bbox_from_points(pts)
            cx = (minx + maxx) / 2.0
            cy = (miny + maxy) / 2.0
            name = getattr(e.dxf, "layer", "") + "_" + f"{len(bays) + 1}"
            bays.append(
                Bay(
                    layer=layer,
                    name=name,
                    minx=minx,
                    miny=miny,
                    maxx=maxx,
                    maxy=maxy,
                    cx=cx,
                    cy=cy,
                )
            )
    # sort bays left-to-right by cx, then bottom-to-top
    bays.sort(key=lambda b: (b.cx, b.cy))
    # assign better names if layers already have names in text: try reading text entities near centroid
    # find text labels near each bay
    for i, b in enumerate(bays):
        # search for TEXT or MTEXT within bay bbox
        labels = []
        for e in msp.query("TEXT MTEXT"):
            lx = e.dxf.insert[0] if hasattr(e.dxf, "insert") else None
            ly = e.dxf.insert[1] if hasattr(e.dxf, "insert") else None
            if lx is None:
                continue
            if b.minx - 1 <= lx <= b.maxx + 1 and b.miny - 1 <= ly <= b.maxy + 1:
                labels.append(getattr(e, "text", getattr(e.dxf, "text", "")))
        if labels:
            bays[i] = b._replace(name=labels[0])
    return bays


def expand_equipment(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            qty = int(float(r.get("Quantity", 1)))
            for i in range(qty):
                rows.append(r.copy())
    return rows


def assign_units_to_bays(bays, equipment_units):
    assignments = []
    if not bays:
        raise RuntimeError("No bays found in DXF")
    n = len(bays)
    for idx, unit in enumerate(equipment_units):
        bay = bays[idx % n]
        out = {
            "BayLayer": bay.layer,
            "BayName": bay.name,
            "BayCX": bay.cx,
            "BayCY": bay.cy,
            "Item": unit.get("Item", ""),
            "Category": unit.get("Category", ""),
            "UnitCost": unit.get("UnitCost", ""),
        }
        assignments.append(out)
    return assignments


def write_outputs(assignments):
    df = pd.DataFrame(assignments)
    csv_out = os.path.join(OUT, "equipment_bay_mapping.csv")
    xlsx_out = os.path.join(OUT, "equipment_bay_mapping.xlsx")
    df.to_csv(csv_out, index=False)
    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Mapping")
    return csv_out, xlsx_out


def main():
    bays = collect_bays()
    print(f"Found {len(bays)} bays")
    ess = expand_equipment(ESS_CSV)
    non = expand_equipment(NON_CSV)
    # combine essential first, then non-essential
    units = ess + non
    assignments = assign_units_to_bays(bays, units)
    csv_out, xlsx_out = write_outputs(assignments)
    print("Wrote mapping:", csv_out, xlsx_out)


if __name__ == "__main__":
    main()
