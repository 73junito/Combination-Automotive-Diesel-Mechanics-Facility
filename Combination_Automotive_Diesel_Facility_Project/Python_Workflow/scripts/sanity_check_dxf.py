import os
from collections import Counter

import ezdxf


def analyze_dxf(path):
    try:
        doc = ezdxf.readfile(path)
    except Exception as exc:
        return {"file": path, "error": str(exc)}
    entities = Counter()
    layer_set = set()
    total = 0
    msp = doc.modelspace()
    for e in msp:
        t = e.dxftype()
        entities[t] += 1
        total += 1
        try:
            layer_set.add(e.dxf.layer)
        except Exception:
            pass
    return {
        "file": os.path.basename(path),
        "layers": len(layer_set),
        "entities_total": total,
        "entities_by_type": dict(entities),
    }


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "outputs", "DXF")
    base = os.path.abspath(base)
    if not os.path.isdir(base):
        print("DXF output folder not found:", base)
        return
    files = [f for f in os.listdir(base) if f.lower().endswith(".dxf")]
    files.sort()
    results = []
    for f in files:
        path = os.path.join(base, f)
        res = analyze_dxf(path)
        results.append(res)

    for r in results:
        if "error" in r:
            print(r["file"], "ERROR:", r["error"])
            continue
        print(r["file"])
        print(f"  Layers: {r['layers']}")
        print(f"  Entities: {r['entities_total']}")
        for t, c in sorted(r["entities_by_type"].items(), key=lambda x: -x[1]):
            print(f"    {t}: {c}")
        print()


if __name__ == "__main__":
    main()
