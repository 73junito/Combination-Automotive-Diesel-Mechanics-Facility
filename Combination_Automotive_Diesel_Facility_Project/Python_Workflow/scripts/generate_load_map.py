#!/usr/bin/env python3
"""Generate an electrical load map overlay from MEP_equipment_schedule.csv.

Outputs a PNG in the repo `docs/MEP_load_map_electrical.png` and a thumbnail.

Usage: run from workspace root with the workspace venv active (or call the venv python).
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

try:
    import ezdxf
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from PIL import Image
except Exception as e:
    print("Missing dependency; ensure ezdxf, matplotlib, and Pillow are installed.", e)
    raise


CSV_PATH = Path("MEP_equipment_schedule.csv")
DXF_PATH = Path(
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/training_facility_plan_layered.dxf"
)
BASE_PNG = Path("Drawings/Previews/facility_layout_full.png")
OUT_PNG = Path("docs/MEP_load_map_electrical.png")
OUT_THUMB = Path("docs/MEP_load_map_electrical.thumb.png")


def parse_loads(csv_path: Path) -> dict:
    loads = {}
    tag_map = {}
    if not csv_path.exists():
        raise SystemExit(f"Equipment CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            bay = (row.get("Bay ID") or "").strip()
            if not bay:
                continue
            raw = (row.get("Electrical Load (kW)") or "").strip()
            try:
                val = float(raw) if raw and raw not in ("---", "") else 0.0
            except Exception:
                # remove trailing non-numeric
                num = "".join(ch for ch in raw if (ch.isdigit() or ch in ".-eE"))
                try:
                    val = float(num) if num else 0.0
                except Exception:
                    val = 0.0
            loads[bay] = loads.get(bay, 0.0) + val
            # detect a short tag/label for this equipment
            tag = (
                row.get("Tag")
                or row.get("Label")
                or row.get("Short Label")
                or row.get("Equipment ID")
                or row.get("Equipment Name")
                or bay
            ).strip()
            tag_map[bay] = tag
    return loads, tag_map


def entity_points(e):
    t = e.dxftype()
    pts = []
    try:
        if t == "LINE":
            pts.append(tuple(e.dxf.start[:2]))
            pts.append(tuple(e.dxf.end[:2]))
        elif t == "LWPOLYLINE":
            for p in e.get_points():
                pts.append((p[0], p[1]))
        elif t == "POLYLINE":
            for v in e.vertices:
                pts.append(tuple(v.dxf.location[:2]))
        elif t == "CIRCLE":
            c = tuple(e.dxf.center[:2])
            r = float(e.dxf.radius)
            pts.append((c[0] - r, c[1] - r))
            pts.append((c[0] + r, c[1] + r))
        elif t == "ARC":
            c = tuple(e.dxf.center[:2])
            r = float(e.dxf.radius)
            pts.append((c[0] - r, c[1] - r))
            pts.append((c[0] + r, c[1] + r))
        elif t in ("TEXT", "MTEXT"):
            try:
                pos = tuple(e.dxf.insert[:2])
                pts.append(pos)
            except Exception:
                pass
    except Exception:
        pass
    return pts


def compute_bbox(doc):
    msp = doc.modelspace()
    xs = []
    ys = []
    for e in msp:
        for x, y in entity_points(e):
            xs.append(x)
            ys.append(y)
    if not xs:
        return (0, 0, 100, 100)
    return (min(xs), min(ys), max(xs), max(ys))


def find_label_positions(doc, bay_ids: list[str]) -> dict:
    msp = doc.modelspace()
    pos_map = {}
    ids_lower = [b.lower() for b in bay_ids]
    for e in msp:
        t = e.dxftype()
        if t in ("TEXT", "MTEXT"):
            try:
                txt = e.text if hasattr(e, "text") else e.get_text()
            except Exception:
                try:
                    txt = e.dxf.text
                except Exception:
                    txt = ""
            txt_s = (txt or "").strip().lower()
            for i, bid in enumerate(ids_lower):
                if not bid:
                    continue
                if bid in txt_s or txt_s in bid:
                    try:
                        pos = tuple(e.dxf.insert[:2])
                        pos_map[bay_ids[i]] = pos
                    except Exception:
                        continue
    return pos_map


def make_load_map():
    loads, tag_map = parse_loads(CSV_PATH)
    if not loads:
        raise SystemExit("No loads found in CSV")

    print("Loads by bay:", loads)

    if not DXF_PATH.exists():
        print("DXF not found; will render simple legend-only image.")

    doc = None
    if DXF_PATH.exists():
        doc = ezdxf.readfile(str(DXF_PATH))
        bbox = compute_bbox(doc)
    else:
        bbox = (0, 0, 100, 100)

    bay_ids = list(loads.keys())
    positions = {}
    if doc:
        positions = find_label_positions(doc, bay_ids)

    # determine vmin/vmax
    vals = [v for v in loads.values()]
    vmax = max(vals) if vals else 1.0
    vmin = 0.0

    # prepare figure
    fig_w, fig_h = 11, 8.5
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    ax = fig.add_subplot(111)

    # draw base png if available
    if BASE_PNG.exists():
        im = Image.open(BASE_PNG)
        ax.imshow(im, extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
    else:
        ax.set_facecolor("white")

    # plot load markers
    xs = []
    ys = []
    cs = []
    sizes = []
    ann_labels = []
    for bay, val in loads.items():
        if bay in positions:
            x, y = positions[bay]
        else:
            # fallback: spread along a line
            idx = bay_ids.index(bay)
            x = bbox[0] + (bbox[2] - bbox[0]) * (
                0.1 + 0.8 * (idx / max(1, len(bay_ids) - 1))
            )
            y = bbox[1] + (bbox[3] - bbox[1]) * 0.5
        xs.append(x)
        ys.append(y)
        cs.append(val)
        sizes.append(200 + (val / vmax) * 1200)
        # use short tag for label display
        short = tag_map.get(bay, bay)
        ann_labels.append(short)
        # keep a tooltip-like line for kW display
        # we'll annotate short tag and kW on the plot

    cmap = plt.get_cmap("jet")
    norm = Normalize(vmin=vmin, vmax=vmax)
    sc = ax.scatter(
        xs,
        ys,
        c=cs,
        s=sizes,
        cmap=cmap,
        norm=norm,
        edgecolors="black",
        linewidths=0.6,
        alpha=0.85,
    )

    # annotate
    for x, y, lab, val in zip(xs, ys, ann_labels, cs):
        ax.text(
            x,
            y + (bbox[3] - bbox[1]) * 0.01,
            lab,
            fontsize=9,
            color="black",
            weight="bold",
            ha="center",
            va="bottom",
        )
        ax.text(
            x,
            y - (bbox[3] - bbox[1]) * 0.01,
            f"{val:.1f} kW",
            fontsize=7,
            color="black",
            ha="center",
            va="top",
        )

    # colorbar and title
    cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Electrical load (kW)")
    ax.set_title("Electrical Load Map — kW per Bay")
    ax.axis("off")
    # compact legend: list up to 8 tag->description pairs from CSV for context
    try:
        # read some descriptive pairs from CSV
        desc_pairs = []
        with CSV_PATH.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                bay = (r.get("Bay ID") or "").strip()
                if not bay:
                    continue
                tag = (
                    r.get("Tag")
                    or r.get("Label")
                    or r.get("Short Label")
                    or r.get("Equipment ID")
                    or r.get("Equipment Name")
                    or bay
                ).strip()
                desc = (
                    r.get("Description")
                    or r.get("Equipment Description")
                    or r.get("Notes")
                    or ""
                ).strip()
                if tag and desc:
                    desc_pairs.append((tag, desc))
                if len(desc_pairs) >= 8:
                    break
        if desc_pairs:
            # draw a small legend box on lower-left
            legend_x = bbox[0] + (bbox[2] - bbox[0]) * 0.02
            legend_y = bbox[1] + (bbox[3] - bbox[1]) * 0.02
            txt = "Tags:\n" + "\n".join(f"{t}: {d}" for t, d in desc_pairs)
            ax.text(
                legend_x,
                legend_y,
                txt,
                fontsize=7,
                color="black",
                va="bottom",
                ha="left",
            )
    except Exception:
        pass

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(OUT_PNG), bbox_inches="tight", dpi=150)
    plt.close(fig)

    # thumbnail
    im = Image.open(OUT_PNG)
    im.thumbnail((600, 600))
    im.save(OUT_THUMB)

    print("WROTE", OUT_PNG)


if __name__ == "__main__":
    make_load_map()
