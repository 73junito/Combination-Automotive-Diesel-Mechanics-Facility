import os
import struct
from pathlib import Path

MODELS = ["bay", "workbench", "two_post_lift"]
ROOT = Path(__file__).resolve().parent.parent
OUT_STEP = ROOT / "outputs" / "models"
OUT_STL = OUT_STEP / "stl"


def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


def parse_stl_bbox(path):
    # returns (minx,miny,minz),(maxx,maxy,maxz)
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 84:
        raise ValueError("STL too small")
    # heuristic: if header starts with 'solid' and file contains '\nfacet', treat as ASCII
    header_start = data[:5].decode("utf-8", errors="ignore").lower()
    as_text = False
    if header_start.startswith("solid") and b"facet" in data:
        try:
            text = data.decode("utf-8")
            as_text = True
        except Exception:
            as_text = False
    if as_text:
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                parts = line.split()
                if len(parts) >= 4:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    mins[0] = min(mins[0], x)
                    mins[1] = min(mins[1], y)
                    mins[2] = min(mins[2], z)
                    maxs[0] = max(maxs[0], x)
                    maxs[1] = max(maxs[1], y)
                    maxs[2] = max(maxs[2], z)
        return tuple(mins), tuple(maxs)
    else:
        # binary STL
        try:
            tri_count = struct.unpack_from("<I", data, 80)[0]
        except Exception:
            # fallback to ascii parsing
            text = data.decode("utf-8", errors="ignore")
            mins = [float("inf")] * 3
            maxs = [float("-inf")] * 3
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("vertex"):
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        mins[0] = min(mins[0], x)
                        mins[1] = min(mins[1], y)
                        mins[2] = min(mins[2], z)
                        maxs[0] = max(maxs[0], x)
                        maxs[1] = max(maxs[1], y)
                        maxs[2] = max(maxs[2], z)
            return tuple(mins), tuple(maxs)
        # parse triangles
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        offset = 84
        for i in range(tri_count):
            if offset + 50 > len(data):
                break
            chunk = data[offset : offset + 50]
            # 12 floats = 48 bytes, then 2 bytes attr
            vals = struct.unpack("<12f", chunk[:48])
            # vertices are vals[3:12]
            vx = (vals[3], vals[6], vals[9])
            vy = (vals[4], vals[7], vals[10])
            vz = (vals[5], vals[8], vals[11])
            verts = [(vx[i], vy[i], vz[i]) for i in range(3)]
            for x, y, z in verts:
                mins[0] = min(mins[0], x)
                mins[1] = min(mins[1], y)
                mins[2] = min(mins[2], z)
                maxs[0] = max(maxs[0], x)
                maxs[1] = max(maxs[1], y)
                maxs[2] = max(maxs[2], z)
            offset += 50
        return tuple(mins), tuple(maxs)


def main():
    rows = []
    for name in MODELS:
        step_path = OUT_STEP / f"{name}.step"
        stl_path = OUT_STL / f"{name}.stl"
        step_size = step_path.stat().st_size if step_path.exists() else None
        stl_size = stl_path.stat().st_size if stl_path.exists() else None
        bbox = None
        if stl_path.exists():
            mins, maxs = parse_stl_bbox(stl_path)
            dims = tuple(maxs[i] - mins[i] for i in range(3))
            bbox = {
                "min": mins,
                "max": maxs,
                "dim": dims,
            }
        rows.append(
            {
                "name": name,
                "step": step_path,
                "stl": stl_path,
                "step_size": step_size,
                "stl_size": stl_size,
                "bbox": bbox,
            }
        )
    # print report
    print("Model report:")
    for r in rows:
        print(f"\nModel: {r['name']}")
        if r["step"] and r["step"].exists():
            print(f" STEP: {r['step']} ({human_size(r['step_size'])})")
        else:
            print(" STEP: missing")
        if r["stl"] and r["stl"].exists():
            print(f" STL: {r['stl']} ({human_size(r['stl_size'])})")
        else:
            print(" STL: missing")
        if r["bbox"]:
            dx, dy, dz = r["bbox"]["dim"]
            print(f" Bounding box (X×Y×Z): {dx:.3f} × {dy:.3f} × {dz:.3f} (assumed mm)")
            print(
                f" Min: ({r['bbox']['min'][0]:.3f}, {r['bbox']['min'][1]:.3f}, {r['bbox']['min'][2]:.3f})"
            )
            print(
                f" Max: ({r['bbox']['max'][0]:.3f}, {r['bbox']['max'][1]:.3f}, {r['bbox']['max'][2]:.3f})"
            )
        else:
            print(" Bounding box: missing (no STL)")


if __name__ == "__main__":
    main()
