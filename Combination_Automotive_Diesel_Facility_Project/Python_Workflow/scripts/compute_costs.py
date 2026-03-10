#!/usr/bin/env python3
"""Compute totals from equipment/furniture/maintenance CSVs and write summary files."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[1] / "outputs" / "Training_Facility_Drawings_v1.1"
)
DATA = ROOT / "Data"
OUT = ROOT / "financials"
OUT.mkdir(parents=True, exist_ok=True)


def sum_csv(fname: str):
    path = DATA / fname
    total = Decimal("0")
    maint = Decimal("0")
    items = []
    if not path.exists():
        return total, maint, items
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                cost = Decimal(str(row.get("TotalCost") or row.get("Cost") or "0"))
            except Exception:
                cost = Decimal("0")
            try:
                m = Decimal(str(row.get("MaintenanceAnnual") or "0"))
            except Exception:
                m = Decimal("0")
            total += cost
            maint += m
            items.append({**row, "TotalCost": str(cost), "MaintenanceAnnual": str(m)})
    return total, maint, items


def write_md_summary(out_md: Path, categories: list[tuple[str, str]]):
    lines = ["# Facility Cost Summary\n"]
    grand = Decimal("0")
    grand_maint = Decimal("0")
    for title, fname in categories:
        total, maint, items = sum_csv(fname)
        lines.append(f"## {title}\n")
        lines.append(f"- Subtotal: ${total:,.2f}\n")
        lines.append(f"- Annual maintenance (explicit): ${maint:,.2f}\n")
        lines.append("\n")
        grand += total
        grand_maint += maint
    lines.append(
        f"## Grand Total\n- Construction/Equipment/Furniture Total: ${grand:,.2f}\n- Annual Maintenance (explicit sum): ${grand_maint:,.2f}\n"
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return grand, grand_maint


def write_csv_items(out_csv: Path, categories: list[tuple[str, str]]):
    # write combined CSV of all items
    all_items = []
    for title, fname in categories:
        _, _, items = sum_csv(fname)
        for it in items:
            it["Category"] = title
            all_items.append(it)
    if not all_items:
        return
    keys = list(all_items[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for it in all_items:
            w.writerow(it)


def main():
    cats = [
        ("Essential Equipment", "essential_equipment.csv"),
        ("Non-Essential Equipment", "nonessential_equipment_with_cost.csv"),
        ("Furniture", "furniture_list.csv"),
        ("Maintenance & Replacement", "maintenance_and_replacement.csv"),
    ]
    md_out = OUT / "total_costs.md"
    csv_out = OUT / "total_costs_items.csv"
    grand, grand_maint = write_md_summary(md_out, cats)
    write_csv_items(csv_out, cats)
    print("WROTE", md_out)
    print("WROTE", csv_out)


if __name__ == "__main__":
    main()
