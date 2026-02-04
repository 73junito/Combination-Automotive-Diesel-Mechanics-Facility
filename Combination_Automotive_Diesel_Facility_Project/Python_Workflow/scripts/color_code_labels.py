"""
Color-code EQUIP_LABELS in DXF based on Category from equipment_bay_mapping_labeled.csv
- Maps each unique Category to an AutoCAD color index and applies it to TEXT/MTEXT in EQUIP_LABELS
- Saves new DXF as facility_layout_colored.dxf
"""

import csv
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
DXF_IN = os.path.join(OUT, "facility_layout_labeled.dxf")
DXF_OUT = os.path.join(OUT, "facility_layout_colored.dxf")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")

# AutoCAD color indices: choose a palette (skip 0=BYLAYER)
COLOR_PALETTE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def load_mapping(path):
    mapping = {}
    categories = []
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            equip = row.get("EquipID", "").strip()
            cat = row.get("Category", "").strip() or "Other"
            mapping[equip] = cat
            if cat not in categories:
                categories.append(cat)
    return mapping, categories


def build_color_map(categories):
    cmap = {}
    for i, cat in enumerate(categories):
        cmap[cat] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
    return cmap


def apply_colors(dxf_in, dxf_out, mapping, color_map):
    if ezdxf is None:
        raise RuntimeError("ezdxf not installed")
    doc = ezdxf.readfile(dxf_in)
    msp = doc.modelspace()
    updated = 0
    for e in msp:
        try:
            if getattr(e.dxf, "layer", "") != "EQUIP_LABELS":
                continue
        except (AttributeError, TypeError):
            continue
        et = e.dxftype()
        text = ""
        if et == "TEXT":
            text = e.dxf.text
        elif et == "MTEXT":
            text = e.text
        else:
            # Some labels could be added as ATTRIB or others; skip
            continue
        # parse EquipID as first token (E###)
        equip_id = text.split()[0] if text else ""
        cat = mapping.get(equip_id)
        if cat:
            color = color_map.get(cat, 7)
            try:
                e.dxf.color = int(color)
                updated += 1
            except (TypeError, ValueError, AttributeError):
                pass
    doc.saveas(dxf_out)
    return updated


def main():
    mapping, categories = load_mapping(MAPPING_CSV)
    color_map = build_color_map(categories)
    updated = apply_colors(DXF_IN, DXF_OUT, mapping, color_map)
    print(f"Categories found: {len(categories)}")
    print("Color map:", color_map)
    print(f"Updated labels: {updated}")


if __name__ == "__main__":
    main()
