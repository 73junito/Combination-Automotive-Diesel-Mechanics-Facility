import zipfile
from pathlib import Path
p = Path(r"C:\Users\rod63\OneDrive\Desktop\Combination Automotive  Diesel Mechanics Facility\Combination_Automotive_Diesel_Facility_Project\Python_Workflow\outputs\portfolio_submission.zip")
if not p.exists():
    print(f"MISSING: {p}")
    raise SystemExit(2)
with zipfile.ZipFile(p) as z:
    names = z.namelist()
    for i, name in enumerate(names, 1):
        print(f"{i:03}: {name}")
    print("\nTOTAL_FILES:", len(names))
    # Basic expected files
    expected = [
        'README.md',
        'portfolio_combined.pdf',
        'portfolio_combined_with_legend.pdf',
        'legend_page.pdf'
    ]
    print('\nCHECKS:')
    for e in expected:
        print(f"- {e}:", 'FOUND' if any(Path(n).name == e for n in names) else 'MISSING')
