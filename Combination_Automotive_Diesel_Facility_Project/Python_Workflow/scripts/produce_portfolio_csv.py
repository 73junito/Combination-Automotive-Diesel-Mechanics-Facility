"""
Produce a portfolio-ready CSV combining bay geometry, assigned items, and costs.
- Reads: facility_layout_labeled.dxf, equipment_bay_mapping_labeled.csv (or equipment_bay_mapping.csv)
- Reads equipment cost details from equipment_lists.xlsx or CSVs
- Outputs: portfolio_equipment_by_bay.csv in outputs
"""

import os
from typing import Any, Optional

import pandas as pd

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[Any] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_IN = os.path.join(OUT, "facility_layout_labeled.dxf")
MAPPING_CSV_A = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")
MAPPING_CSV_B = os.path.join(OUT, "equipment_bay_mapping.csv")
EQUIP_XLSX = os.path.join(OUT, "equipment_lists.xlsx")
PORTFOLIO_CSV = os.path.join(OUT, "portfolio_equipment_by_bay.csv")


def collect_bays_from_dxf(path):
    if ezdxf is None:
        raise RuntimeError("ezdxf not installed")
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    bays = []
    for e in msp:
        etype = e.dxftype()
        layer = getattr(e.dxf, "layer", "")
        if etype in ("LWPOLYLINE", "POLYLINE") and layer in (
            "AUTO_BAYS",
            "DIESEL_BAYS",
        ):
            try:
                pts = (
                    list(e.get_points())
                    if hasattr(e, "get_points")
                    else [tuple(v) for v in e.vertices()]
                )
            except AttributeError:
                pts = [tuple(v) for v in e.vertices()]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
            cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
            bays.append(
                {
                    "BayLayer": layer,
                    "BayName": None,  # mapping provides name; fallback later
                    "MinX": minx,
                    "MinY": miny,
                    "MaxX": maxx,
                    "MaxY": maxy,
                    "BayCX": cx,
                    "BayCY": cy,
                    "BayWidth": maxx - minx,
                    "BayHeight": maxy - miny,
                }
            )
    return bays


def load_mapping():
    csv_path = MAPPING_CSV_A if os.path.exists(MAPPING_CSV_A) else MAPPING_CSV_B
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Mapping CSV not found")
    df = pd.read_csv(csv_path)
    return df


def load_equipment_costs():
    # prefer equipment_lists.xlsx, else combine CSVs
    if os.path.exists(EQUIP_XLSX):
        xls = pd.ExcelFile(EQUIP_XLSX)
        dfs = {}
        for s in xls.sheet_names:
            dfs[s] = xls.parse(s)
        equip_df = pd.concat(dfs.values(), ignore_index=True)
    else:
        # try essential + nonessential
        ess = os.path.join(OUT, "essential_equipment.csv")
        non = os.path.join(OUT, "nonessential_equipment.csv")
        parts = []
        if os.path.exists(ess):
            parts.append(pd.read_csv(ess))
        if os.path.exists(non):
            parts.append(pd.read_csv(non))
        if not parts:
            raise FileNotFoundError("No equipment cost files found")
        equip_df = pd.concat(parts, ignore_index=True)
    # normalize column names
    equip_df.columns = [c.strip() for c in equip_df.columns]
    return equip_df


def build_portfolio():
    mapping = load_mapping()
    costs = load_equipment_costs()
    # prepare costs key by Item (best-effort match)
    costs_key = costs.set_index("Item")[["UnitCost"]].to_dict()["UnitCost"]

    # if BayName missing in mapping, attempt to set using BayLayer sequence
    if "BayName" not in mapping.columns or mapping["BayName"].isnull().all():
        mapping["BayName"] = (
            mapping["BayLayer"]
            + "_"
            + (mapping.groupby("BayLayer").cumcount() + 1).astype(str)
        )

    # collect bay centroids from DXF for geometry reference
    bays = collect_bays_from_dxf(DXF_IN)
    # build quick lookup by approximate (BayLayer, BayCX) matching
    bay_lookup = {}
    for b in bays:
        key = (b["BayLayer"], round(b["BayCX"], 1))
        bay_lookup[key] = b

    rows = []
    for _, row in mapping.iterrows():
        bay_layer = row.get("BayLayer")
        bay_name = row.get("BayName")
        # attempt to find bay by name; fall back to nearest cx
        bay = None
        # try exact match by BayName against mapping of bays from earlier scripts
        # Many bays are named like AUTO_BAYS_1 etc. Try to parse index
        if bay_name:
            # find bay in bays list by name pattern
            for b in bays:
                # Skip fragile BayName pattern matching; will match by centroid below
                break
        # fallback match by layer and nearest center x
        try:
            cx = float(row.get("BayCX", 0))
            key = (bay_layer, round(cx, 1))
            bay = bay_lookup.get(key)
        except (TypeError, ValueError):
            bay = None
        # if still None, try any bay with same layer
        if bay is None:
            for b in bays:
                if b["BayLayer"] == bay_layer:
                    bay = b
                    break
        # assemble portfolio row
        unit_cost = row.get("UnitCost")
        if pd.isna(unit_cost) or unit_cost == "" or unit_cost is None:
            # try lookup by item name
            item = row.get("Item", "")
            unit_cost = costs_key.get(item, "")
        rows.append(
            {
                "EquipID": row.get("EquipID", ""),
                "BayLayer": bay_layer,
                "BayName": bay_name,
                "BayCX": (
                    row.get("BayCX", "")
                    if "BayCX" in row
                    else (bay["BayCX"] if bay else "")
                ),
                "BayCY": (
                    row.get("BayCY", "")
                    if "BayCY" in row
                    else (bay["BayCY"] if bay else "")
                ),
                "BayWidth": bay["BayWidth"] if bay else "",
                "BayHeight": bay["BayHeight"] if bay else "",
                "Item": row.get("Item", ""),
                "Category": row.get("Category", ""),
                "UnitCost": unit_cost,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(PORTFOLIO_CSV, index=False)
    return PORTFOLIO_CSV, df


def main():
    out, df = build_portfolio()
    print("Wrote portfolio CSV:", out)
    print("Sample rows:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
