#!/usr/bin/env python3
"""
Export a high-resolution PNG of the master layered DXF with selectable layers,
legend and a callout box.

Usage:
  python export_master_png.py --in <dxf> --out <png> --dpi 300 \
    --layers ARCH,EQUIP,ELEC,M-EXHAUST,P-* \
    --callout "Mechanical scope limited to exhaust..."
"""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

try:
    import ezdxf
except Exception:
    raise SystemExit("Requires ezdxf: python -m pip install ezdxf")


def layer_matches(layer: str, patterns: list[str]) -> bool:
    for p in patterns:
        if fnmatch.fnmatch(layer, p):
            return True
    return False


def collect_entities(doc, patterns):
    msp = doc.modelspace()
    ents = []
    layers_seen = set()
    for e in msp:
        try:
            layer = e.dxf.layer
        except Exception:
            layer = ""
        if layer_matches(layer, patterns):
            ents.append((e, layer))
            layers_seen.add(layer)
    return ents, sorted(layers_seen)


def render(ents, layers_seen, out_path: Path, dpi: int, callout: str):
    fig = plt.figure(figsize=(11.0, 8.5))  # landscape by default
    ax = fig.add_subplot(111)

    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    def _update_bounds(x, y):
        nonlocal minx, miny, maxx, maxy
        minx = min(minx, x)
        miny = min(miny, y)
        maxx = max(maxx, x)
        maxy = max(maxy, y)

    # color mapping: prefix/pattern -> (color, description)
    color_map = [
        ("A-*", "#2b83ba", "Architecture (walls, doors, grid)"),
        ("E-*", "#d7191c", "Electrical (power, panels, lighting)"),
        ("P-*", "#fdae61", "Plumbing (water, drains)"),
        ("M-*", "#abdda4", "Mechanical (vents, exhaust)"),
        ("EQ-*", "#8c510a", "Equipment (lifts, toolboxes)"),
        ("FURN-*", "#7f3b08", "Furniture/fixtures"),
        ("ROOM-*", "#6a51a3", "Room labels / text"),
    ]

    def choose_color(layer_name: str):
        for pattern, col, _desc in color_map:
            if fnmatch.fnmatch(layer_name, pattern):
                return col
        # fallback: assign a color based on hash for variety
        cols = ["#000000", "#555555", "#1b9e77", "#e7298a", "#66a61e"]
        return cols[hash(layer_name) % len(cols)]

    for e, layer in ents:
        et = e.dxftype()
        col = choose_color(layer)
        if et == "LINE":
            x1, y1, *_ = e.dxf.start
            x2, y2, *_ = e.dxf.end
            ax.plot([x1, x2], [y1, y2], color=col, linewidth=0.8)
            _update_bounds(x1, y1)
            _update_bounds(x2, y2)
        elif et in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(p[0], p[1]) for p in e.get_points()]
            except Exception:
                try:
                    points = [(p[0], p[1]) for p in e.points()]
                except Exception:
                    points = []
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                ax.plot(xs, ys, color=col, linewidth=0.8)
                for x, y in points:
                    _update_bounds(x, y)
        elif et == "CIRCLE":
            cx, cy, _ = e.dxf.center
            r = float(e.dxf.radius)
            circ = plt.Circle((cx, cy), r, fill=False, edgecolor=col, linewidth=0.8)
            ax.add_patch(circ)
            _update_bounds(cx - r, cy - r)
            _update_bounds(cx + r, cy + r)
        elif et in ("TEXT", "MTEXT"):
            try:
                txt = e.text if hasattr(e, "text") else e.get_text()
            except Exception:
                try:
                    txt = e.dxf.text
                except Exception:
                    txt = ""
            try:
                x, y = (e.dxf.insert[0], e.dxf.insert[1])
            except Exception:
                x, y = (0, 0)
            # render text in darker shade for readability
            ax.text(x, y, txt, fontsize=6, color="#111111")
            _update_bounds(x, y)

    if minx == float("inf"):
        minx = miny = -10
        maxx = maxy = 10

    pad_x = (maxx - minx) * 0.04 if maxx > minx else 1
    pad_y = (maxy - miny) * 0.04 if maxy > miny else 1
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_aspect("equal")
    ax.axis("off")

    # Legend box (bottom-right) with color swatches and short descriptions
    bbox_props = dict(
        boxstyle="round,pad=0.3", facecolor="white", edgecolor="black", alpha=0.95
    )
    # build legend lines from color_map
    legend_lines = []
    for pattern, col, desc in color_map:
        legend_lines.append((col, pattern.replace("*", ""), desc))

    # draw legend manually (tweaked sizing for better thumbnail readability)
    leg_x = 0.68
    leg_y = 0.04
    line_h = 0.04
    sw = 0.03
    # draw background box
    ax.text(
        leg_x - 0.01,
        leg_y + line_h * (len(legend_lines) + 0.5),
        "",
        transform=ax.transAxes,
        bbox=bbox_props,
    )
    for i, (col, name, desc) in enumerate(legend_lines):
        y = leg_y + line_h * (len(legend_lines) - i - 1)
        # swatch
        rect = Rectangle(
            (leg_x, y),
            sw,
            line_h * 0.85,
            transform=ax.transAxes,
            facecolor=col,
            edgecolor="black",
            linewidth=0.5,
        )
        ax.add_patch(rect)
        ax.text(
            leg_x + sw + 0.01,
            y + 0.001,
            f"{name}: {desc}",
            transform=ax.transAxes,
            fontsize=9,
            va="bottom",
        )

    # Callout box (top-right)
    callout_text = callout or ""
    ax.text(
        0.99,
        0.98,
        callout_text,
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="right",
        bbox=bbox_props,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", dest="out", required=True)
    p.add_argument("--dpi", dest="dpi", type=int, default=300)
    p.add_argument("--layers", dest="layers", default="ARCH,EQUIP,ELEC,M-EXHAUST,P-*")
    p.add_argument("--callout", dest="callout", default="")
    args = p.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    patterns = [s.strip() for s in args.layers.split(",") if s.strip()]

    doc = ezdxf.readfile(str(inp))
    ents, layers_seen = collect_entities(doc, patterns)

    render(ents, layers_seen, out, args.dpi, args.callout)
    print("WROTE PNG:", out)


if __name__ == "__main__":
    main()
