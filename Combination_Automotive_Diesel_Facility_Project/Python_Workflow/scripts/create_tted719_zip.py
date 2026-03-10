import sys
import zipfile
from pathlib import Path

ROOT = Path(
    r"C:/Users/rod63/OneDrive/Desktop/Combination Automotive  Diesel Mechanics Facility/Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/Training_Facility_Drawings_v1.1"
)
FILES = [
    "training_facility_plan_layered.dxf",
    "facility_layout_full.pdf",
    "manifest.md",
    "checksums.sha256",
    "portfolio_final.pdf",
    "outputs/auto_diesel_facility.blend",
]
OUT = ROOT / "TTED719_Facility_Design_Rodriguez_v1.1.zip"

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
    print("Skipped (missing):", file=sys.stderr)
    for s in skipped:
        print(f" - {s}", file=sys.stderr)
