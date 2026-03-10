"""Quick DXF reviewer checks for ARCH and EQUIP discipline files.

Outputs a concise summary: layer counts, entity counts, and equipment label tallies
to support a reviewer-eye quality check.
"""

import os
import re
from typing import Any

import ezdxf


def analyze(path: str) -> dict[str, Any]:
    doc = ezdxf.readfile(path)
    layers: set[str] = set()
    type_counts: dict[str, int] = {}
    texts: list[str] = []
    for e in doc.modelspace():
        layers.add(e.dxf.layer)
        t = e.dxftype()
        type_counts[t] = type_counts.get(t, 0) + 1
        if t == "TEXT":
            texts.append(getattr(e.dxf, "text", ""))
    return {
        "path": path,
        "layers": sorted(list(layers)),
        "layer_count": len(layers),
        "type_counts": type_counts,
        "texts": texts,
    }


def tally_labels(texts):
    counts = {"L-Bay": 0, "H-Bay": 0, "EV Charger": 0, "TB": 0}
    for t in texts:
        if re.search(r"L-Bay\s*\d+", t):
            counts["L-Bay"] += 1
        if re.search(r"H-Bay\s*\d+", t):
            counts["H-Bay"] += 1
        if re.search(r"EV Charger", t, re.I):
            counts["EV Charger"] += 1
        if re.search(r"\bTB\s*\d+", t):
            counts["TB"] += 1
    return counts


def main():
    base = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "outputs", "DXF")
    )
    arch = os.path.join(base, "ARCH_Plan.dxf")
    equip = os.path.join(base, "EQUIP_Plan.dxf")
    results = {}
    for p in [arch, equip]:
        if not os.path.exists(p):
            print(f"Missing file: {p}")
            return
        results[os.path.basename(p)] = analyze(p)

    for name, r in results.items():
        print(f"\n{name}")
        print(f"  Layers: {r['layer_count']}")
        print(f"  Layers list: {', '.join(r['layers'])}")
        total_entities = sum(r["type_counts"].values())
        print(f"  Entities: {total_entities}")
        for t, c in r["type_counts"].items():
            print(f"    {t}: {c}")
        if name == "EQUIP_Plan.dxf":
            labels = tally_labels(r["texts"])
            print("  Equipment label counts:")
            for k, v in labels.items():
                print(f"    {k}: {v}")

    # Also analyze master layered DXF for label counts and exact equipment occurrences
    master = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "outputs",
            "training_facility_plan_layered.dxf",
        )
    )
    if os.path.exists(master):
        m = analyze(master)
        print("\nMaster layered DXF:")
        print(f"  Layers: {m['layer_count']}")
        # count EQ-LIFT and EQ-CHARGE occurrences from master
        eq_lift = 0
        eq_charge = 0
        tb = 0
        h_bay = 0
        for t in m["texts"]:
            if re.search(r"L-Bay\s*\d+", t):
                eq_lift += 1
            if re.search(r"H-Bay\s*\d+", t):
                h_bay += 1
            if re.search(r"EV Charger", t, re.I):
                eq_charge += 1
            if re.search(r"\bTB\s*\d+", t):
                tb += 1
        print(f"  L-Bay labels (master): {eq_lift}")
        print(f"  H-Bay labels (master): {h_bay}")
        print(f"  EV Charger labels (master): {eq_charge}")
        print(f"  Toolbox labels (master): {tb}")


if __name__ == "__main__":
    main()
