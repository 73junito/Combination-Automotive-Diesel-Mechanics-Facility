"""
Replace TEXT/MTEXT labels on EQUIP_LABELS with block references.
- Creates one block per `EquipID` containing a small rectangle and center text with the EquipID.
- Inserts block at original label location on layer `EQUIP_LABELS` and applies color per Category mapping.
- Saves output as `facility_layout_blocks.dxf` in the `outputs` folder.
"""

import csv
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
DXF_IN = os.path.join(OUT, "facility_layout_colored.dxf")
DXF_OUT = os.path.join(OUT, "facility_layout_blocks.dxf")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")

# Block visual parameters (units consistent with drawing)
BLOCK_W = 10.0
BLOCK_H = 6.0
TEXT_HEIGHT = 3.0

COLOR_PALETTE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def load_mapping(path):
    mapping = {}
    categories = []
    if not os.path.exists(path):
        return mapping, categories
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


def create_block_def(doc, name, equip_id):
    # create a new block with a centered rectangle and a text entity
    if name in doc.blocks:
        return
    blk = doc.blocks.new(name=name)
    w = BLOCK_W
    h = BLOCK_H
    pts = [
        (-w / 2, -h / 2),
        (w / 2, -h / 2),
        (w / 2, h / 2),
        (-w / 2, h / 2),
        (-w / 2, -h / 2),
    ]
    # rectangle as lightweight polyline (BYBLOCK color)
    try:
        blk.add_lwpolyline(pts, dxfattribs={"closed": True, "color": 256})
    except AttributeError:
        # fallback to polyline2d
        blk.add_polyline2d(pts, dxfattribs={"color": 256})
    # add centered TEXT (BYBLOCK color)
    try:
        txt = blk.add_text(equip_id, dxfattribs={"height": TEXT_HEIGHT, "color": 256})
        # Place at block origin center
        try:
            txt.set_pos((0, 0), align="MIDDLE_CENTER")
        except AttributeError:
            # fallback: set raw insert
            txt.dxf.insert = (0, -TEXT_HEIGHT / 3)
    except (AttributeError, TypeError):
        # ignore text creation errors
        pass


def main():
    if ezdxf is None:
        print("ezdxf not installed")
        return
    if not os.path.exists(DXF_IN):
        print("Input DXF not found:", DXF_IN)
        return
    mapping, categories = load_mapping(MAPPING_CSV)
    color_map = build_color_map(categories)

    doc = ezdxf.readfile(DXF_IN)
    msp = doc.modelspace()
    inserts_created = 0
    removed = 0
    created_blocks = set()

    # iterate a copy of modelspace entities list to allow deletion
    entities = list(msp)
    for e in entities:
        try:
            layer = e.dxf.layer
        except AttributeError:
            continue
        if layer != "EQUIP_LABELS":
            continue
        et = e.dxftype()
        text = ""
        insert_point = None
        if et == "TEXT":
            text = e.dxf.text
            insert_point = tuple(e.dxf.insert)
        elif et == "MTEXT":
            text = e.text
            try:
                insert_point = tuple(e.dxf.insert)
            except AttributeError:
                # MTEXT fallback: use e.get_location() if available
                try:
                    insert_point = tuple(e.insert)
                except AttributeError:
                    insert_point = None
        else:
            continue
        if not text or not insert_point:
            continue
        equip_id = text.split()[0]
        block_name = f"BLK_{equip_id}"
        if block_name not in created_blocks:
            create_block_def(doc, block_name, equip_id)
            created_blocks.add(block_name)
        # determine color from mapping
        cat = mapping.get(equip_id)
        color = color_map.get(cat, 7)
        # insert block
        try:
            msp.add_blockref(
                block_name,
                insert_point,
                dxfattribs={"layer": "EQUIP_LABELS", "color": int(color)},
            )
            inserts_created += 1
        except (ValueError, TypeError, AttributeError, OSError) as ex:
            print("Failed to insert", block_name, "at", insert_point, "error:", ex)
            continue
        # remove original text entity
        try:
            msp.delete_entity(e)
            removed += 1
        except (AttributeError, KeyError, OSError):
            # try destroy
            try:
                e.destroy()
                removed += 1
            except (AttributeError, OSError):
                pass

    doc.saveas(DXF_OUT)
    print("Blocks created:", len(created_blocks))
    print("Insertions:", inserts_created)
    print("Original labels removed:", removed)
    print("Color map:", color_map)


if __name__ == "__main__":
    main()
