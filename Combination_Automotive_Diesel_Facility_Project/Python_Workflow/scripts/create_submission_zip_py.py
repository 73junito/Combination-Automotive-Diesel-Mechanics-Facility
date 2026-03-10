import sys
import zipfile
from pathlib import Path

root = Path(
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/Training_Facility_Drawings_v1.1"
)
files = [
    "training_facility_plan_layered.dxf",
    "facility_layout_full.pdf",
    "manifest.md",
    "checksums.sha256",
    "portfolio_final.pdf",
    "outputs/auto_diesel_facility.blend",
]
zip_path = root / "facility_submission_v1.1_py.zip"

root.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for rel in files:
        p = root / rel
        if p.exists():
            # keep the relative path inside the zip
            z.write(p, arcname=rel)
        else:
            print(f"Warning: missing file, skipping: {p}", file=sys.stderr)

print(f"Created: {zip_path}")
