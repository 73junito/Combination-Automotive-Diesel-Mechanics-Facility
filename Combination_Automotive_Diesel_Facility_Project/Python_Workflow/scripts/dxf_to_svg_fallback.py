#!/usr/bin/env python3
"""
Fallback DXF -> SVG/PNG exporter using ezdxf + matplotlib.

This is a best-effort renderer that handles basic DXF entities (LINE, LWPOLYLINE,
POLYLINE, CIRCLE, ARC, TEXT). It produces a vector SVG and a PNG raster fallback.

Usage:
  python dxf_to_svg_fallback.py input.dxf output.svg [output.png]
"""

import math
import sys
from pathlib import Path

try:
    import ezdxf
    import matplotlib.pyplot as plt
    from ezdxf.entities import (Arc, Circle, Line, LWPolyline, MText, Polyline,
                                Text)
    from matplotlib.collections import LineCollection
except ImportError:
    print("Missing dependency: ensure 'ezdxf' and 'matplotlib' are installed.")
    raise


def sample_arc(center, radius, start_angle, end_angle, segments=64):
    # start/end in degrees
    start = math.radians(start_angle)
    end = math.radians(end_angle)
    if end < start:
        end += 2 * math.pi
    pts = []
    for i in range(segments + 1):
        t = start + (end - start) * (i / segments)
        x = center[0] + math.cos(t) * radius
        y = center[1] + math.sin(t) * radius
        pts.append((x, y))
    return pts


def entity_lines(entity):
    """Return sequence(s) of points for plotting for a given entity."""
    etype = entity.dxftype()
    if etype == "LINE":
        return [[tuple(entity.dxf.start), tuple(entity.dxf.end)]]
    if etype == "LWPOLYLINE":
        pts = [tuple(p[:2]) for p in entity.get_points()]
        return [pts]
    if etype == "POLYLINE":
        pts = [tuple(v.dxf.location[:2]) for v in entity.vertices]
        return [pts]
    if etype == "CIRCLE":
        c = tuple(entity.dxf.center)
        r = float(entity.dxf.radius)
        return [sample_arc(c, r, 0, 360, segments=128)]
    if etype == "ARC":
        c = tuple(entity.dxf.center)
        r = float(entity.dxf.radius)
        sa = float(entity.dxf.start_angle)
        ea = float(entity.dxf.end_angle)
        return [sample_arc(c, r, sa, ea, segments=64)]
    # unsupported -> ignore
    return []


def collect_text(entity):
    etype = entity.dxftype()
    if etype == "TEXT":
        pos = tuple(entity.dxf.insert[:2])
        return [(pos, entity.dxf.text)]
    if etype == "MTEXT":
        pos = tuple(entity.dxf.insert[:2])
        return [(pos, entity.text)]
    return []


def bounding_box(lines):
    xs = []
    ys = []
    for seg in lines:
        for x, y in seg:
            xs.append(x)
            ys.append(y)
    if not xs:
        return (0, 0, 1, 1)
    return (min(xs), min(ys), max(xs), max(ys))


from typing import Optional


def render(dxf_path: Path, out_svg: Path, out_png: Optional[Path] = None, dpi=300):
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    lines = []
    texts = []
    for e in msp:
        try:
            lines.extend(entity_lines(e))
            texts.extend(collect_text(e))
        except AttributeError:
            # skip entities missing expected attributes
            continue

    if not lines:
        print("No drawable entities found in DXF.")

    # flatten for bbox
    minx, miny, maxx, maxy = bounding_box(lines)
    width = maxx - minx if maxx > minx else 1.0
    height = maxy - miny if maxy > miny else 1.0

    fig = plt.figure(figsize=(max(6, width / 100), max(4, height / 100)), dpi=dpi)
    ax = fig.add_subplot(111)

    # Prepare line segments for LineCollection
    segs = [seg for seg in lines if len(seg) >= 2]
    if segs:
        lc = LineCollection(segs, colors="black", linewidths=0.6)
        ax.add_collection(lc)

    # add text
    for pos, txt in texts:
        ax.text(pos[0], pos[1], txt, fontsize=6, color="black")

    ax.set_xlim(minx - width * 0.02, maxx + width * 0.02)
    ax.set_ylim(miny - height * 0.02, maxy + height * 0.02)
    ax.set_aspect("equal")
    ax.axis("off")

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving SVG: {out_svg}")
    fig.savefig(str(out_svg), format="svg", bbox_inches="tight", pad_inches=0)
    if out_png:
        print(f"Saving PNG: {out_png}")
        fig.savefig(
            str(out_png), format="png", dpi=dpi, bbox_inches="tight", pad_inches=0
        )
    plt.close(fig)


def main(argv):
    if len(argv) < 3:
        print("Usage: dxf_to_svg_fallback.py input.dxf output.svg [output.png]")
        return 2
    in_p = Path(argv[1])
    out_svg = Path(argv[2])
    out_png = Path(argv[3]) if len(argv) > 3 else out_svg.with_suffix(".png")
    if not in_p.exists():
        print(f"Input DXF not found: {in_p}")
        return 2
    try:
        render(in_p, out_svg, out_png)
        print("Export complete.")
        return 0
    except Exception as e:
        print("Rendering failed:", e)
        raise


if __name__ == "__main__":
    sys.exit(main(sys.argv))
