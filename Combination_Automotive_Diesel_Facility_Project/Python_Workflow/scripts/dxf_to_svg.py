#!/usr/bin/env python3
"""
Simple DXF -> SVG converter using ezdxf and matplotlib as a fallback.

Usage:
  python scripts/dxf_to_svg.py --in-dir <disciplines_dir> --out-dir <viewer/assets/cad_svg>

Notes:
 - Preferred: ezdxf's matplotlib qsave backend (if available) is used.
 - Fallback: basic plotting for LINE/LWPOLYLINE/POLYLINE/CIRCLE/TEXT to SVG via matplotlib.
 - This is intended for read-only preview SVGs (not a perfect CAD renderer).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

try:
    import ezdxf
except Exception as e:
    print(
        "ezdxf is required. Install with: python -m pip install ezdxf", file=sys.stderr
    )
    raise


def qsave_svg_fallback(doc, out_path: Path) -> bool:
    """Attempt to use ezdxf matplotlib qsave if available. Returns True on success."""
    try:
        from ezdxf.addons.drawing.matplotlib import qsave

        # qsave accepts a modelspace or a drawing object depending on ezdxf version
        try:
            qsave(doc.modelspace(), str(out_path))
        except Exception:
            qsave(doc, str(out_path))
        return True
    except Exception:
        return False


def fallback_draw_svg(doc, out_path: Path) -> None:
    """Basic fallback renderer using matplotlib for common entities."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Arc, Circle
    except Exception:
        print(
            "matplotlib is required for fallback rendering. Install with: python -m pip install matplotlib",
            file=sys.stderr,
        )
        raise

    msp = doc.modelspace()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    def _update_bounds(x, y):
        nonlocal minx, miny, maxx, maxy
        if x is None or y is None:
            return
        minx = min(minx, x)
        miny = min(miny, y)
        maxx = max(maxx, x)
        maxy = max(maxy, y)

    for e in msp:
        et = e.dxftype()
        if et == "LINE":
            x1, y1, *_ = e.dxf.start
            x2, y2, *_ = e.dxf.end
            ax.plot([x1, x2], [y1, y2], color="black", linewidth=0.6)
            _update_bounds(x1, y1)
            _update_bounds(x2, y2)
        elif et in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(p[0], p[1]) for p in e.get_points()]
            except Exception:
                points = [(p[0], p[1]) for p in e.points()]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, color="black", linewidth=0.6)
            for x, y in points:
                _update_bounds(x, y)
        elif et == "CIRCLE":
            cx, cy, _ = e.dxf.center
            r = float(e.dxf.radius)
            circ = Circle((cx, cy), r, fill=False, edgecolor="black", linewidth=0.6)
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
            ax.text(x, y, txt, fontsize=6)
            _update_bounds(x, y)
        # ignore other types for now

    if minx == float("inf"):
        minx = miny = -10
        maxx = maxy = 10

    padding_x = (maxx - minx) * 0.05 if maxx > minx else 1
    padding_y = (maxy - miny) * 0.05 if maxy > miny else 1
    ax.set_xlim(minx - padding_x, maxx + padding_x)
    ax.set_ylim(miny - padding_y, maxy + padding_y)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.savefig(str(out_path), format="svg", bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def convert_file(inp: Path, out: Path) -> None:
    print(f"Converting: {inp} -> {out}")
    doc = ezdxf.readfile(str(inp))
    out.parent.mkdir(parents=True, exist_ok=True)
    # try qsave first
    ok = qsave_svg_fallback(doc, out)
    if ok:
        print("Used ezdxf matplotlib qsave backend for SVG.")
        return
    # fallback
    print("Falling back to basic matplotlib renderer (may be lossy).")
    fallback_draw_svg(doc, out)


def main() -> None:
    p = argparse.ArgumentParser(description="DXF -> SVG preview generator")
    p.add_argument(
        "--in-dir",
        dest="in_dir",
        required=True,
        help="Directory containing DXF files to convert",
    )
    p.add_argument(
        "--out-dir", dest="out_dir", required=True, help="Directory for output SVGs"
    )
    p.add_argument(
        "--pattern",
        dest="pattern",
        default="*_only.dxf",
        help="Filename glob pattern to convert",
    )
    args = p.parse_args()

    inp = Path(args.in_dir)
    outd = Path(args.out_dir)
    if not inp.exists():
        raise SystemExit(f"Input dir not found: {inp}")
    outd.mkdir(parents=True, exist_ok=True)

    files = sorted(inp.glob(args.pattern))
    if not files:
        print("No DXF files found for pattern", args.pattern)

    for f in files:
        out_name = f.stem + ".svg"
        out_path = outd / out_name
        try:
            convert_file(f, out_path)
        except Exception as e:
            print("Failed to convert", f, "->", e, file=sys.stderr)


if __name__ == "__main__":
    main()
