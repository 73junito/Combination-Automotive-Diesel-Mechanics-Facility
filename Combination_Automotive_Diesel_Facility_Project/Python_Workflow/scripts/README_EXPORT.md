export_cost_pdfs.ps1
=====================

Purpose
-------
Small PowerShell helper to export common cost tables (CSV/XLSX) into the five PDFs expected by the grading rubric.

Behavior
--------
- Looks for likely source files under the repository (CSV/XLSX common names). See the `mappings` in the script.
- First attempts to use Excel COM automation (best fidelity). If Excel isn't available, falls back to LibreOffice headless (`soffice`) if on PATH.
- Writes PDFs into `Python_Workflow/scripts/outputs` by default.

Usage examples
--------------
# Basic run (defaults):
.\Python_Workflow\scripts\export_cost_pdfs.ps1

# Force overwrite existing PDFs and use LibreOffice explicitly (auto-detect on PATH):
.\Python_Workflow\scripts\export_cost_pdfs.ps1 -Force -UseLibreOffice

# If LibreOffice is installed but not on PATH (example on Windows):
.\Python_Workflow\scripts\export_cost_pdfs.ps1 -Force -UseLibreOffice -LibreOfficePath "C:\Program Files\LibreOffice"

Notes
-----
- If your sources are named differently, either rename them to the expected names or edit the script `mappings` array.
- The script attempts minimal page setup (landscape, fit to width). If you need custom formatting, open the source in Excel and adjust before export.
