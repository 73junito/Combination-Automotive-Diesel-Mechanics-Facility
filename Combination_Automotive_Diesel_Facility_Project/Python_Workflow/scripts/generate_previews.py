"""Generate simple PNG previews from exported DXF discipline files.

This script reads LWPOLYLINE and TEXT entities from DXF files in
`../outputs/DXF/` and renders them to PNGs in `../outputs/previews/`.

Usage: run from repo root with the project's virtualenv active.
Dependencies: ezdxf, matplotlib
"""

import os
import math
import ezdxf
import matplotlib.pyplot as plt


def collect_entities(doc):
    polys = []
    texts = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t == "LWPOLYLINE":
            try:
                pts = [
                    (p[0], p[1]) if len(p) >= 2 else (p[0], 0) for p in e.get_points()
                ]
                polys.append(pts)
            except Exception:
                continue
        elif t == "TEXT":
            try:
                txt = getattr(e.dxf, "text", "")
                insert = getattr(e.dxf, "insert", (0, 0))
                height = float(getattr(e.dxf, "height", 0.3))
                texts.append((txt, insert[0], insert[1], height))
            except Exception:
                continue
    return polys, texts


def bounds_from_polys(polys, texts):
    xs = []
    ys = []
    for pts in polys:
        for x, y in pts:
            xs.append(x)
            ys.append(y)
    for _, x, y, _ in texts:
        xs.append(x)
        ys.append(y)
    if not xs or not ys:
        return (0, 0, 10, 10)
    minx = min(xs)
    maxx = max(xs)
    miny = min(ys)
    maxy = max(ys)
    # add padding
    dx = maxx - minx if maxx - minx != 0 else 1.0
    dy = maxy - miny if maxy - miny != 0 else 1.0
    pad = max(dx, dy) * 0.05
    return (minx - pad, miny - pad, maxx + pad, maxy + pad)


def render_preview(dxf_path, out_path):
    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        print(f"Failed to read {dxf_path}: {e}")
        return False

    polys, texts = collect_entities(doc)
    minx, miny, maxx, maxy = bounds_from_polys(polys, texts)

    width = maxx - minx
    height = maxy - miny
    if width == 0 or height == 0:
        width, height = 10, 10

    # figure size tuned for readability
    dpi = 150
    fig_w = max(6, width / max(width, height) * 8)
    fig_h = max(6, height / max(width, height) * 8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_facecolor("white")

    # draw polylines
    for pts in polys:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs, ys, color="black", linewidth=1)

    # draw texts
    for txt, x, y, h in texts:
        ax.text(x, y, txt, fontsize=max(6, h * 6), color="black")

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"Saved preview: {out_path}")
    return True


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "outputs")
    base = os.path.abspath(base)
    dxf_dir = os.path.join(base, "DXF")
    out_dir = os.path.join(base, "previews")
    if not os.path.isdir(dxf_dir):
        print(f"DXF directory not found: {dxf_dir}")
        return

    files = [f for f in os.listdir(dxf_dir) if f.upper().endswith(".DXF")]
    if not files:
        print("No DXF files found to preview")
        return

    for f in files:
        name = os.path.splitext(f)[0]
        dxf_path = os.path.join(dxf_dir, f)
        out_path = os.path.join(out_dir, f"{name}.png")
        render_preview(dxf_path, out_path)


if __name__ == "__main__":
    main()
