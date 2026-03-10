#!/usr/bin/env python3
"""Generate a full-size PDF from the master layered DXF.

Usage:
  python generate_full_plan_pdf.py <input.dxf> <output.pdf>

This uses ezdxf + matplotlib (Agg) to render DXF entities and write a PDF.
"""

import math
import sys
from pathlib import Path

try:
    import ezdxf
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
except Exception as exc:
    print("Missing dependency: ensure 'ezdxf' and 'matplotlib' are installed.")
    raise


def sample_arc(center, radius, start_angle, end_angle, segments=64):
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


def render_to_pdf(dxf_path: Path, out_pdf: Path, dpi=300, spread_layers: bool = False):
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    # Group entities by layer so we can optionally offset per-layer for visibility
    layer_lines = {}
    layer_texts = {}
    for e in msp:
        try:
            layer = getattr(e.dxf, "layer", "")
        except Exception:
            layer = ""
        layer_lines.setdefault(layer, [])
        layer_texts.setdefault(layer, [])
        try:
            for seg in entity_lines(e):
                layer_lines[layer].append(seg)
            for t in collect_text(e):
                layer_texts[layer].append(t)
        except Exception:
            continue

    # Flatten all lines to compute bounds
    all_lines = [seg for segs in layer_lines.values() for seg in segs]
    if not all_lines:
        print("No drawable entities found in DXF.")

    minx, miny, maxx, maxy = bounding_box(all_lines)
    width = maxx - minx if maxx > minx else 1.0
    height = maxy - miny if maxy > miny else 1.0

    # scale figure size to content (in inches)
    fig_w = max(11, width / 100)
    fig_h = max(8.5, height / 100)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    ax = fig.add_subplot(111)

    layers = list(sorted(layer_lines.keys()))

    # Determine offset step when spreading layers (tweakable multiplier)
    # Increasing the multiplier gives more horizontal separation between layers
    offset_step = width * 0.06 if spread_layers and len(layers) > 1 else 0.0

    for idx, layer in enumerate(layers):
        dx = idx * offset_step
        segs = [seg for seg in layer_lines.get(layer, []) if len(seg) >= 2]
        if segs:
            # apply horizontal translation for visibility when requested
            translated = [[(x + dx, y) for (x, y) in seg] for seg in segs]
            lc = LineCollection(translated, colors="black", linewidths=0.6)
            ax.add_collection(lc)

        for pos, txt in layer_texts.get(layer, []):
            try:
                ax.text(pos[0] + dx, pos[1], txt, fontsize=6, color="black")
            except Exception:
                continue

    # Expand bounds to include spread offsets
    total_width = width + offset_step * max(0, len(layers) - 1)
    ax.set_xlim(minx - total_width * 0.02, minx + total_width + total_width * 0.02)
    ax.set_ylim(miny - height * 0.02, maxy + height * 0.02)
    ax.set_aspect("equal")
    ax.axis("off")

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving PDF: {out_pdf}")
    fig.savefig(str(out_pdf), format="pdf", bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def main(argv):
    if len(argv) < 3:
        print("Usage: generate_full_plan_pdf.py input.dxf output.pdf")
        return 2
    in_p = Path(argv[1])
    out_p = Path(argv[2])
    if not in_p.exists():
        print(f"Input DXF not found: {in_p}")
        return 2
    try:
        render_to_pdf(in_p, out_p)
        print("Export complete.")
        return 0
    except Exception as e:
        print("Rendering failed:", e)
        raise


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
