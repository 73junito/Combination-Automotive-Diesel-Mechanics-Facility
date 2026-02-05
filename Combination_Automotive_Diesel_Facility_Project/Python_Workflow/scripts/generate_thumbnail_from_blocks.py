"""
Generate a thumbnail PNG from `facility_layout_blocks.dxf` by rendering polylines and block inserts.
Saves `facility_layout_thumbnail.png` to the outputs folder.
"""

import os
from types import ModuleType
from typing import Any, Optional

# annotate ezdxf so mypy sees it may be None
ezdxf: Optional[ModuleType] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
except ImportError:
    ezdxf = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_BLOCKS = os.path.join(OUT, "facility_layout_blocks.dxf")
THUMB = os.path.join(OUT, "facility_layout_thumbnail.png")
THUMB_PDF = os.path.join(OUT, "facility_layout_thumbnail.pdf")
THUMB_SVG = os.path.join(OUT, "facility_layout_thumbnail.svg")

BLOCK_W = 10.0
BLOCK_H = 6.0

# Simple AutoCAD color index -> RGB map (approximate)
ACAD_COLOR_RGB = {
    1: (1.0, 0.0, 0.0),  # red
    2: (1.0, 1.0, 0.0),  # yellow
    3: (0.0, 0.0, 1.0),  # blue
    4: (1.0, 0.5, 0.0),  # orange
    5: (0.5, 0.0, 0.5),  # purple
    6: (0.0, 0.5, 0.0),  # green
    7: (0.8, 0.8, 0.8),  # light gray
}


def draw_polylines(ax: Any, entities: Any) -> None:
    for e in entities:
        t = e.dxftype()
        try:
            if t == "LWPOLYLINE":
                pts = list(e.get_points())
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.plot(xs, ys, color="black", linewidth=0.8, alpha=0.7)
            elif t == "POLYLINE":
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices()]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.plot(xs, ys, color="black", linewidth=0.8, alpha=0.7)
            elif t == "LINE":
                x1, y1 = e.dxf.start[0], e.dxf.start[1]
                x2, y2 = e.dxf.end[0], e.dxf.end[1]
                ax.plot([x1, x2], [y1, y2], color="black", linewidth=0.6, alpha=0.6)
        except AttributeError:
            continue


def main() -> None:
    if ezdxf is None:
        print("ezdxf or matplotlib not installed")
        return
    if not os.path.exists(DXF_BLOCKS):
        print("DXF not found:", DXF_BLOCKS)
        return
    doc = ezdxf.readfile(DXF_BLOCKS)
    msp = doc.modelspace()

    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    # draw structural polylines (WALLS, AUTO_BAYS, DIESEL_BAYS) for context
    layers_for_structure = ["WALLS", "AUTO_BAYS", "DIESEL_BAYS"]
    struct_entities = [
        e for e in msp if getattr(e.dxf, "layer", "") in layers_for_structure
    ]
    draw_polylines(ax, struct_entities)

    # draw all polylines as faint background
    other_polys = [
        e
        for e in msp
        if e.dxftype() in ("LWPOLYLINE", "POLYLINE", "LINE")
        and getattr(e.dxf, "layer", "") not in layers_for_structure
    ]
    draw_polylines(ax, other_polys)

    # draw block inserts from EQUIP_LABELS
    inserts = [
        e
        for e in msp
        if e.dxftype() == "INSERT" and getattr(e.dxf, "layer", "") == "EQUIP_LABELS"
    ]
    for ins in inserts:
        x, y, z = ins.dxf.insert
        color_idx = getattr(ins.dxf, "color", 7)
        rgb = ACAD_COLOR_RGB.get(int(color_idx), (0.2, 0.2, 0.2))
        # Rectangle centered at insert
        rect = Rectangle(
            (x - BLOCK_W / 2, y - BLOCK_H / 2),
            BLOCK_W,
            BLOCK_H,
            facecolor=rgb,
            edgecolor="black",
            linewidth=0.6,
            alpha=0.9,
        )
        ax.add_patch(rect)
        # text
        ax.text(
            x,
            y,
            ins.dxf.name.replace("BLK_", ""),
            ha="center",
            va="center",
            fontsize=6,
            color="white",
        )

    ax.set_aspect("equal")
    ax.axis("off")

    # autoscale
    all_x = []
    all_y = []
    for e in struct_entities + other_polys:
        try:
            if e.dxftype() == "LWPOLYLINE":
                pts = list(e.get_points())
                all_x += [p[0] for p in pts]
                all_y += [p[1] for p in pts]
            elif e.dxftype() == "POLYLINE":
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices()]
                all_x += [p[0] for p in pts]
                all_y += [p[1] for p in pts]
            elif e.dxftype() == "LINE":
                all_x += [e.dxf.start[0], e.dxf.end[0]]
                all_y += [e.dxf.start[1], e.dxf.end[1]]
        except AttributeError:
            continue
    for ins in inserts:
        all_x.append(ins.dxf.insert[0])
        all_y.append(ins.dxf.insert[1])

    if all_x and all_y:
        margin = 20
        xmin, xmax = min(all_x) - margin, max(all_x) + margin
        ymin, ymax = min(all_y) - margin, max(all_y) + margin
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

    fig.savefig(THUMB, bbox_inches="tight", pad_inches=0)
    try:
        fig.savefig(THUMB_PDF, format="pdf", bbox_inches="tight", pad_inches=0)
        print("Vector PDF written to", THUMB_PDF)
    except OSError:
        print("Failed to write vector PDF (fallback PNG only)")
    try:
        fig.savefig(THUMB_SVG, format="svg", bbox_inches="tight", pad_inches=0)
        print("Vector SVG written to", THUMB_SVG)
    except OSError:
        print("Failed to write SVG")
    plt.close(fig)
    print("Thumbnail written to", THUMB)


if __name__ == "__main__":
    main()
