import zipfile
from pathlib import Path

ROOT = Path(
    r"C:/Users/rod63/OneDrive/Desktop/Combination Automotive  Diesel Mechanics Facility/Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/Training_Facility_Drawings_v1.1"
)
FILES = [
    "training_facility_plan_layered.dxf",
    "facility_layout_engineering.dxf",
    "facility_layout_full.pdf",
    "facility_layout_labeled.dxf",
    "facility_layout_colored.dxf",
    "portfolio_final.pdf",
    "portfolio_combined_with_legend.pdf",
    "essential_equipment.csv",
    "nonessential_equipment.csv",
    "equipment_lists.xlsx",
    "equipment_bay_mapping.xlsx",
    "Vendor_Procurement_Master.xls",
    "manifest.md",
    "checksums.sha256",
    "SUBMISSION_CHECKLIST.md",
    "totalcost_per_bay.png",
]
OUT = ROOT / "TTED719_Facility_Design_Rodriguez_v1.1_complete.zip"

added = []
skipped = []
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        p = ROOT / f
        if p.exists():
            z.write(p, arcname=f)
            added.append(f)
        else:
            skipped.append(f)

print(f"ZIP created: {OUT}")
print("Added files:")
for a in added:
    print(f" - {a}")
if skipped:
    print("Skipped (missing):")
    for s in skipped:
        print(f" - {s}")

# list contents
with zipfile.ZipFile(OUT) as z:
    print("\nZIP contents:")
    for name in z.namelist():
        print(name)
