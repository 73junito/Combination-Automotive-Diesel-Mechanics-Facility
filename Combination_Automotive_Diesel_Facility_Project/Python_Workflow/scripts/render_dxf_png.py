#!/usr/bin/env python3
"""
Render a DXF to PNG (matplotlib) and perform a simple alignment check between
geometry (LWPOLYLINE/LINE) and `ROOM-LABEL` text inserts.

Usage:
  python render_dxf_png.py --in <dxf> --out <png>

Prints a short alignment summary to stdout.
"""

from __future__ import annotations

import argparse
import math
import statistics
from pathlib import Path

try:
    import ezdxf
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
except Exception as e:
    raise SystemExit(
        "Requires ezdxf and matplotlib: python -m pip install ezdxf matplotlib"
    )


def centroid_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys)) if points else (0.0, 0.0)


def collect_geom_and_labels(doc):
    msp = doc.modelspace()
    poly_centroids = []
    line_centroids = []
    label_positions = []

    for e in msp:
        et = e.dxftype()
        if et in ("LWPOLYLINE", "POLYLINE"):
            try:
                pts = [(float(p[0]), float(p[1])) for p in e.get_points()]
            except Exception:
                try:
                    pts = [(float(v[0]), float(v[1])) for v in e.points()]
                except Exception:
                    pts = []
            if pts:
                poly_centroids.append(centroid_of_points(pts))
        elif et == "LINE":
            s = e.dxf.start
            ept = e.dxf.end
            line_centroids.append(((s[0] + ept[0]) / 2.0, (s[1] + ept[1]) / 2.0))
        elif et in ("TEXT", "MTEXT"):
            try:
                pos = e.dxf.insert
                label_positions.append((float(pos[0]), float(pos[1])))
            except Exception:
                pass

    return poly_centroids + line_centroids, label_positions


def analyze_alignment(geoms, labels):
    if not geoms or not labels:
        return {"status": "insufficient_data", "details": "no geometry or no labels"}

    # For each geometry centroid, find nearest label and compute vector
    vectors = []
    dists = []
    for gx, gy in geoms:
        best = min(labels, key=lambda p: (p[0] - gx) ** 2 + (p[1] - gy) ** 2)
        vx, vy = best[0] - gx, best[1] - gy
        vectors.append((vx, vy))
        dists.append(math.hypot(vx, vy))

    median_dx = statistics.median([v[0] for v in vectors])
    median_dy = statistics.median([v[1] for v in vectors])
    median_dist = statistics.median(dists)
    mean_dist = statistics.mean(dists)

    # compute residual scatter after removing median translation
    residuals = [math.hypot(v[0] - median_dx, v[1] - median_dy) for v in vectors]
    rms_resid = math.sqrt(sum(r * r for r in residuals) / len(residuals))

    status = "aligned"
    # thresholds (units are DXF drawing units): tweak as needed
    if median_dist > 20:
        status = "offset"
    elif rms_resid > 5:
        status = "possible_rotation_or_scale"

    return {
        "status": status,
        "median_translation": (median_dx, median_dy),
        "median_distance": median_dist,
        "mean_distance": mean_dist,
        "rms_residual": rms_resid,
        "samples": len(geoms),
    }


def render_png(doc, out_path: Path):
    msp = doc.modelspace()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    def _update_bounds(x, y):
        nonlocal minx, miny, maxx, maxy
        minx = min(minx, x)
        miny = min(miny, y)
        maxx = max(maxx, x)
        maxy = max(maxy, y)

    for e in msp:
        et = e.dxftype()
        if et == "LINE":
            x1, y1, *_ = e.dxf.start
            x2, y2, *_ = e.dxf.end
            ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.0)
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
                ax.plot(xs, ys, color="black", linewidth=1.0)
                for x, y in points:
                    _update_bounds(x, y)
        elif et == "CIRCLE":
            cx, cy, _ = e.dxf.center
            r = float(e.dxf.radius)
            circ = Circle((cx, cy), r, fill=False, edgecolor="black", linewidth=1.0)
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
            x, y = (
                (e.dxf.insert[0], e.dxf.insert[1])
                if hasattr(e.dxf, "insert")
                else (0, 0)
            )
            ax.text(x, y, txt, fontsize=6, color="white")
            _update_bounds(x, y)

    if minx == float("inf"):
        minx = miny = -10
        maxx = maxy = 10

    pad_x = (maxx - minx) * 0.05 if maxx > minx else 1
    pad_y = (maxy - miny) * 0.05 if maxy > miny else 1
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_aspect("equal")
    ax.axis("off")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", dest="out", required=True)
    args = p.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")

    doc = ezdxf.readfile(str(inp))
    geoms, labels = collect_geom_and_labels(doc)
    report = analyze_alignment(geoms, labels)

    print("Alignment report:")
    for k, v in report.items():
        print(f"  {k}: {v}")

    render_png(doc, out)
    print("WROTE PNG:", out)


if __name__ == "__main__":
    main()
