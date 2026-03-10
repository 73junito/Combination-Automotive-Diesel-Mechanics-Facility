# Drawing Catalog — README

This file explains how `Drawings/catalog.md` is generated and how to regenerate it locally.

What the catalog contains
- An auto-generated index of drawings found in the repository (or from exported PDFs).
- Clickable thumbnails link to full-size preview images stored under `Drawings/Previews/`.

How to regenerate (local)
1. Ensure Python dependencies are available. From the repo root, you can use the workspace venv:

```powershell
python -m pip install --user pymupdf Pillow
```

2. Generate previews (scans one or more PDF locations and writes PNG + thumbnails into `Drawings/Previews/`):

```powershell
python scripts/generate_previews.py --pdf-dir "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs" --preview-dir Drawings/Previews
```

You can repeat `--pdf-dir` to scan additional folders (for example `Drawings/Exports/PDFs`).

3. Regenerate the catalog markdown:

```powershell
python scripts/generate_catalog.py --cad-dir Drawings/CAD --preview-dir Drawings/Previews --output Drawings/catalog.md
```

Notes
- CI already runs preview generation and catalog creation as part of the `cad-exports` workflow; you only need to run the above steps locally to regenerate the catalog for local preview.
- The generator attempts to detect revisions from filenames (e.g. `_rev02`) and groups items by project/discipline heuristics; extend `project_map` in `scripts/generate_catalog.py` to add friendly names.
- If you prefer not to install external tools, the preview generator will use Python fallbacks (`PyMuPDF` + `Pillow`) when installed.

How to contribute
- When adding or updating drawings, commit the source and exports, then run the preview + catalog commands above and commit the updated `Drawings/Previews/` and `Drawings/catalog.md` so the catalog stays in sync.

Support
- If previews fail to generate, ensure `pdftoppm` or ImageMagick is available on PATH, or install `pymupdf` and `Pillow` into your Python environment.
