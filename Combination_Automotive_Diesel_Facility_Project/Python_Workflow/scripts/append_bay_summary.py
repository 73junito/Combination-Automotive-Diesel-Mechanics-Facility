"""
Append per-bay cost summary to portfolio_equipment_by_bay.xlsx
- Reads: portfolio_equipment_by_bay.csv
- Writes: portfolio_equipment_by_bay.xlsx with sheets:
    - Detailed (full rows)
    - Bay Summary (per-bay totals, counts)
"""

import os
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
CSV_IN = os.path.join(OUT, "portfolio_equipment_by_bay.csv")
XLSX_OUT = os.path.join(OUT, "portfolio_equipment_by_bay.xlsx")


def main():
    if not os.path.exists(CSV_IN):
        raise FileNotFoundError(f"Input CSV not found: {CSV_IN}")
    df = pd.read_csv(CSV_IN)
    # Ensure UnitCost numeric
    df["UnitCost"] = pd.to_numeric(df["UnitCost"], errors="coerce").fillna(0.0)

    # Bay summary
    summary = df.groupby(["BayLayer", "BayName"], as_index=False).agg(
        ItemCount=("EquipID", "count"), TotalCost=("UnitCost", "sum")
    )
    # add average cost per item
    summary["AverageCost"] = (summary["TotalCost"] / summary["ItemCount"]).round(2)

    # Write to Excel with two sheets
    with pd.ExcelWriter(XLSX_OUT, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Detailed", index=False)
        summary.to_excel(writer, sheet_name="Bay Summary", index=False)

    print("Wrote", XLSX_OUT)
    print("\nBay Summary sample:")
    print(summary.head().to_string(index=False))


if __name__ == "__main__":
    main()
