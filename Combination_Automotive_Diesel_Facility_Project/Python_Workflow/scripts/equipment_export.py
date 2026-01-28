"""
Export equipment and cost tables (CSV + Excel) to outputs folder.
Generates:
 - essential_equipment.csv
 - nonessential_equipment.csv
 - equipment_lists.xlsx (two sheets)

Run with workspace venv python.
"""

import os
from datetime import date
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.normpath(os.path.join(ROOT, "Python_Workflow", "outputs"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample essential equipment list
ESSENTIAL = [
    {
        "Category": "Lift",
        "Item": "Two-post lift",
        "Quantity": 10,
        "UnitCost": 2500.0,
        "MaintenanceAnnual": 150.0,
        "ReplacementYears": 15,
    },
    {
        "Category": "Compressor",
        "Item": "Air compressor (50 CFM)",
        "Quantity": 2,
        "UnitCost": 8000.0,
        "MaintenanceAnnual": 300.0,
        "ReplacementYears": 20,
    },
    {
        "Category": "Diagnostics",
        "Item": "Scan tool (shop)",
        "Quantity": 4,
        "UnitCost": 1200.0,
        "MaintenanceAnnual": 50.0,
        "ReplacementYears": 7,
    },
    {
        "Category": "Welding",
        "Item": "MIG welder",
        "Quantity": 2,
        "UnitCost": 1200.0,
        "MaintenanceAnnual": 75.0,
        "ReplacementYears": 12,
    },
]

# Sample non-essential equipment list
NONESSENTIAL = [
    {
        "Category": "Advanced Diagnostics",
        "Item": "Oscilloscope",
        "Quantity": 1,
        "UnitCost": 3500.0,
        "MaintenanceAnnual": 100.0,
        "ReplacementYears": 10,
    },
    {
        "Category": "Simulator",
        "Item": "Engine simulator",
        "Quantity": 1,
        "UnitCost": 15000.0,
        "MaintenanceAnnual": 500.0,
        "ReplacementYears": 10,
    },
    {
        "Category": "OEM Tools",
        "Item": "Brand-specific dealer kit",
        "Quantity": 2,
        "UnitCost": 5000.0,
        "MaintenanceAnnual": 200.0,
        "ReplacementYears": 8,
    },
]


def compute_totals(rows):
    df = pd.DataFrame(rows)
    df["TotalCost"] = df["Quantity"] * df["UnitCost"]
    df["AnnualMaintenanceTotal"] = df["Quantity"] * df["MaintenanceAnnual"]
    return df


def export_csv(df, filename):
    out = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(out, index=False)
    return out


def export_excel(dfs: dict, filename: str):
    out = os.path.join(OUTPUT_DIR, filename)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    return out


def main():
    ess_df = compute_totals(ESSENTIAL)
    non_df = compute_totals(NONESSENTIAL)

    ess_csv = export_csv(ess_df, "essential_equipment.csv")
    non_csv = export_csv(non_df, "nonessential_equipment.csv")
    xlsx = export_excel({"Essential": ess_df, "NonEssential": non_df}, "equipment_lists.xlsx")

    summary = {
        "essential_csv": ess_csv,
        "nonessential_csv": non_csv,
        "excel": xlsx,
        "generated_date": date.today().isoformat(),
    }

    print("Generated equipment exports:")
    for k, v in summary.items():
        print(f" - {k}: {v}")

    # Print simple totals
    print("\nTotals:")
    print(f" Essential total cost: ${ess_df['TotalCost'].sum():,.2f}")
    print(f" Non-essential total cost: ${non_df['TotalCost'].sum():,.2f}")


if __name__ == "__main__":
    main()
