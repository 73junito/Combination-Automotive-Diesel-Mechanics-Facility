"""
Write equipment labels into DXF based on equipment_bay_mapping.csv.
- Generates EquipID for each mapped unit (if missing)
- Places TEXT labels inside each bay (positions distributed across bay width)
- Saves new DXF: facility_layout_labeled.dxf
- Writes updated mapping CSV/XLSX with `EquipID` column
"""

import os
from collections import defaultdict
from types import ModuleType
from typing import Any, Optional

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[ModuleType] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_IN = os.path.join(OUT, "facility_layout_sample.dxf")
DXF_OUT = os.path.join(OUT, "facility_layout_labeled.dxf")
# Optional layered output with equipment labels on dedicated layer
LABEL_LAYER = "EQUIP_LABELS"
# AutoCAD color index: 1=red,2=yellow,3=green,4=cyan,5=blue,6=magenta,7=white
LABEL_COLOR_INDEX = 2
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping.csv")
MAPPING_XLSX = os.path.join(OUT, "equipment_bay_mapping_labeled.xlsx")

if ezdxf is None:
    raise RuntimeError("ezdxf not installed in venv")


class Bay:
    def __init__(self, layer, name, minx, miny, maxx, maxy, cx, cy):
        self.layer = layer
        self.name = name
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.cx = cx
        self.cy = cy
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny


def bbox_from_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def collect_bays_from_dxf(doc):
    msp = doc.modelspace()
    bays = []
    for e in msp:
        etype = e.dxftype()
        layer = getattr(e.dxf, "layer", "")
        if etype in ("LWPOLYLINE", "POLYLINE") and layer in (
            "AUTO_BAYS",
            "DIESEL_BAYS",
        ):
            # get points
            try:
                pts = (
                    list(e.get_points())
                    if hasattr(e, "get_points")
                    else [tuple(v) for v in e.vertices()]
                )
            except AttributeError:
                pts = [tuple(v) for v in e.vertices()]
            minx, miny, maxx, maxy = bbox_from_points(pts)
            cx = (minx + maxx) / 2.0
            cy = (miny + maxy) / 2.0
            # name based on layer occurrence count
            name = f"{layer}_{len(bays) + 1}"
            bays.append(Bay(layer, name, minx, miny, maxx, maxy, cx, cy))
    # sort by cx then cy
    bays.sort(key=lambda b: (b.cx, b.cy))
    # reassign deterministic names after sort
    for i, b in enumerate(bays):
        b.name = f"{b.layer}_{i + 1}"
    return bays


def read_mapping(csv_path):
    df = pd.read_csv(csv_path)
    return df


def write_updated_mapping(df, csv_out, xlsx_out):
    df.to_csv(csv_out, index=False)
    with pd.ExcelWriter(xlsx_out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Mapping", index=False)


def place_labels(doc, bays, mapping_df, text_layer="TEXT_LABELS"):
    msp = doc.modelspace()
    # ensure label layer exists with chosen color
    if LABEL_LAYER not in doc.layers:
        try:
            doc.layers.new(name=LABEL_LAYER, dxfattribs={"color": LABEL_COLOR_INDEX})
        except (AttributeError, ValueError):
            # older ezdxf/dxf versions might require different creation; ignore if fails
            pass
    # group mapping by BayName
    groups = defaultdict(list)
    for _, row in mapping_df.iterrows():
        groups[row["BayName"]].append(row)
    # for each bay, compute positions across width
    for b in bays:
        items = groups.get(b.name, [])
        n = len(items)
        if n == 0:
            continue
        # spacing with margin inside bay
        margin = min(2.0, b.width * 0.05)
        avail_width = max(1.0, b.width - 2 * margin)
        spacing = avail_width / (n + 1)
        positions = []
        for i in range(n):
            x = b.minx + margin + spacing * (i + 1)
            y = b.cy  # center vertically
            positions.append((x, y))
        # add text for each item
        for item, row in zip(items, positions):
            label = f"{item['EquipID']} {item['Item']}"
            # write label on dedicated equipment label layer for clarity
            txt = msp.add_text(label, dxfattribs={"layer": LABEL_LAYER, "height": 2.5})
            txt.dxf.insert = row
    return doc


def main():
    # read mapping
    df = read_mapping(MAPPING_CSV)
    # add EquipID if missing
    if "EquipID" not in df.columns:
        df["EquipID"] = [f"E{str(i + 1).zfill(3)}" for i in range(len(df))]
    # open dxf
    doc = ezdxf.readfile(DXF_IN)
    bays = collect_bays_from_dxf(doc)
    # place labels
    doc = place_labels(doc, bays, df)
    # save new dxf
    doc.saveas(DXF_OUT)
    # write updated mapping
    write_updated_mapping(
        df, os.path.join(OUT, "equipment_bay_mapping_labeled.csv"), MAPPING_XLSX
    )
    print("Wrote labeled DXF:", DXF_OUT)
    print("Wrote labeled mapping CSV/XLSX")


if __name__ == "__main__":
    main()
