"""
Add engineering-ready annotation layers and export CSV/XLSX tables.
- Reads `equipment_bay_mapping_labeled.csv`
- Creates layers: `STRUCTURAL_ANNOT`, `MECH_ANNOT`, `ELEC_SCHEMATIC`
- Adds text annotations per bay (slab thickness, equipment weight, airflow, electrical load)
- Writes CSVs: `structural_loads.csv`, `mechanical_services.csv`, `electrical_loads.csv`
- Saves DXF as `facility_layout_engineering.dxf`

Notes: uses conservative placeholder assumptions; each CSV contains an `Assumption` column for engineer review.
"""

import csv
import os
from typing import Any, Optional
from types import ModuleType
from collections import defaultdict

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[ModuleType] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")
DXF_IN = os.path.join(OUT, "facility_layout_blocks.dxf")
DXF_OUT = os.path.join(OUT, "facility_layout_engineering.dxf")
STRUCT_CSV = os.path.join(OUT, "structural_loads.csv")
MECH_CSV = os.path.join(OUT, "mechanical_services.csv")
ELEC_CSV = os.path.join(OUT, "electrical_loads.csv")

# Placeholder assumed weights (lbs) and loads (kW) by Category
ASSUMED_WEIGHT = {
    "Lift": 2500,
    "Compressor": 500,
    "Diagnostics": 50,
    "Welding": 300,
    "Advanced Diagnostics": 100,
    "Simulator": 800,
    "OEM Tools": 200,
}
ASSUMED_LOAD_KW = {
    "Lift": 1.5,
    "Compressor": 7.5,
    "Diagnostics": 0.5,
    "Welding": 5.0,
    "Advanced Diagnostics": 3.5,
    "Simulator": 15.0,
    "OEM Tools": 2.0,
}
# Mechanical airflow placeholders by bay type inferred from BayName
MECH_AIRFLOW = {
    "DIESEL": 1500,  # Diesel exhaust cfm
    "AUTO": 500,  # lift area cfm
}
DEFAULT_SLAB_IN = 8.0


def read_mapping(path: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows.append(row)
    return rows


def group_by_bay(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    bybay: defaultdict = defaultdict(list)
    for r in rows:
        bybay[r["BayName"]].append(r)
    return bybay


def write_csv_structural(path: str, bay_summaries: dict[str, dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "BayName",
                "BayCX",
                "BayCY",
                "SlabThickness_in",
                "TotalEquipmentWeight_lbs",
                "Assumptions",
            ]
        )
        for b, s in bay_summaries.items():
            w.writerow(
                [
                    b,
                    s["cx"],
                    s["cy"],
                    s["slab_in"],
                    int(s["total_weight"]),
                    "Assumed weights per category. Verify with vendor.",
                ]
            )


def write_csv_mech(path: str, bay_mech: dict[str, list[dict[str, Any]]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["BayName", "ServiceType", "Value", "Units", "Assumptions"])
        for b, mech in bay_mech.items():
            for svc in mech:
                w.writerow(
                    [b, svc["type"], svc["value"], svc["units"], svc["assumption"]]
                )


def write_csv_elec(path: str, elec_rows: list[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["BayName", "EquipID", "Item", "Load_kW", "CircuitID", "Assumptions"]
        )
        for r in elec_rows:
            w.writerow(
                [
                    r["bay"],
                    r["equip"],
                    r["item"],
                    r["load_kw"],
                    r["circuit"],
                    r["assump"],
                ]
            )


def annotate_dxf(
    dxf_in: str,
    dxf_out: str,
    bay_summaries: dict[str, dict[str, Any]],
    bay_mech: dict[str, list[dict[str, Any]]],
    elec_rows: list[dict[str, Any]],
) -> None:
    if ezdxf is None:
        print("ezdxf not available; skipping DXF annotation")
        return
    doc = ezdxf.readfile(dxf_in)
    msp = doc.modelspace()
    # ensure layers exist
    for ln in ("STRUCTURAL_ANNOT", "MECH_ANNOT", "ELEC_SCHEMATIC"):
        if ln not in doc.layers:
            doc.layers.new(ln)
    # place structural text
    for b, s in bay_summaries.items():
        x, y = float(s["cx"]) + 6.0, float(s["cy"]) + 6.0
        t = f"Slab: {s['slab_in']} in\nW: {int(s['total_weight'])} lb"
        # use simple TEXT lines (multiple lines separated)
        for i, line in enumerate(t.split("\n")):
            tx = msp.add_text(
                line, dxfattribs={"height": 2.5, "layer": "STRUCTURAL_ANNOT"}
            )
            try:
                tx.set_pos((x, y - i * 3), align="LEFT")
            except AttributeError:
                # fallback for ezdxf versions: set insert directly
                tx.dxf.insert = (x, y - i * 3)
    # mechanical annotations
    for b, mechs in bay_mech.items():
        # place at bay center offset
        s = bay_summaries[b]
        x, y = float(s["cx"]) - 6.0, float(s["cy"]) + 6.0
        for i, svc in enumerate(mechs):
            line = f"{svc['type']}: {svc['value']} {svc['units']}"
            tx = msp.add_text(line, dxfattribs={"height": 2.5, "layer": "MECH_ANNOT"})
            try:
                tx.set_pos((x, y - i * 3), align="LEFT")
            except AttributeError:
                tx.dxf.insert = (x, y - i * 3)
    # electrical annotations
    for r in elec_rows:
        b = r["bay"]
        s = bay_summaries[b]
        x, y = float(s["cx"]) - 6.0, float(s["cy"]) - 6.0
        line = f"Elec load: {r['load_kw']} kW ({r['circuit']})"
        tx = msp.add_text(line, dxfattribs={"height": 2.5, "layer": "ELEC_SCHEMATIC"})
        try:
            tx.set_pos((x, y), align="LEFT")
        except AttributeError:
            tx.dxf.insert = (x, y)
    doc.saveas(dxf_out)
    print("Wrote annotated DXF:", dxf_out)


def main() -> None:
    rows = read_mapping(MAPPING_CSV)
    if not rows:
        print("No mapping rows found at", MAPPING_CSV)
        return
    bybay = group_by_bay(rows)
    bay_summaries = {}
    bay_mech = {}
    elec_rows = []
    for bay, items in bybay.items():
        # take bay center from first row
        cx = items[0].get("BayCX", "0")
        cy = items[0].get("BayCY", "0")
        slab_in = DEFAULT_SLAB_IN
        total_weight = 0.0
        for it in items:
            cat = (it.get("Category") or "Other").strip()
            equip = it.get("EquipID", "")
            itemname = it.get("Item", "")
            w = ASSUMED_WEIGHT.get(cat, 100)
            total_weight += w
            load_kw = ASSUMED_LOAD_KW.get(cat, 0.5)
            # electrical row
            elec_rows.append(
                {
                    "bay": bay,
                    "equip": equip,
                    "item": itemname,
                    "load_kw": load_kw,
                    "circuit": f"C_{bay}",
                    "assump": "Placeholder load; verify",
                }
            )
        bay_summaries[bay] = {
            "cx": cx,
            "cy": cy,
            "slab_in": slab_in,
            "total_weight": total_weight,
        }
        # mechanical services: infer from bay name prefix
        mech_list = []
        if bay.upper().startswith("DIESEL"):
            mech_list.append(
                {
                    "type": "Diesel exhaust",
                    "value": MECH_AIRFLOW["DIESEL"],
                    "units": "CFM",
                    "assumption": "Preliminary",
                }
            )
        else:
            mech_list.append(
                {
                    "type": "Lift area airflow",
                    "value": MECH_AIRFLOW["AUTO"],
                    "units": "CFM",
                    "assumption": "Preliminary",
                }
            )
        bay_mech[bay] = mech_list

    write_csv_structural(STRUCT_CSV, bay_summaries)
    write_csv_mech(MECH_CSV, bay_mech)
    write_csv_elec(ELEC_CSV, elec_rows)
    print("Wrote CSVs:", STRUCT_CSV, MECH_CSV, ELEC_CSV)

    annotate_dxf(DXF_IN, DXF_OUT, bay_summaries, bay_mech, elec_rows)


if __name__ == "__main__":
    main()
