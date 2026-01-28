This folder contains helper scripts for producing Blender-friendly SVGs and rendering a clean viewport image.

Files:
- `convert_dxf_to_svg.ps1`  - PowerShell script that uses Inkscape CLI to convert DXF → SVG (Windows).
- `blender_import_and_render.py` - Blender automation script to import SVG, center/scale, add a note, and render a PNG.

Usage examples (PowerShell):

Convert a DXF to SVG with Inkscape:

```powershell
# from repository root (adjust paths as needed)
.
\Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\convert_dxf_to_svg.ps1 -InputPath "Drawings\CAD\layout.dxf" -OutputPath "outputs\layout.svg"
```

Render the SVG to a PNG using Blender (headless):

```powershell
# Example: run from repo root, adjust Blender path if needed
"C:\Program Files\Blender Foundation\Blender\blender.exe" --background --python "Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\blender_import_and_render.py" -- "Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\outputs\layout.svg" "Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\outputs\layout.png" --res 3840 2160 --apply-scale
```

Notes & guardrails:
- Do NOT overwrite submission ZIPs or original CAD files — produce outputs in a separate `outputs/` folder.
- If Inkscape or Blender is not in PATH, pass full executable paths or install them.
- The Blender script tries to enable the SVG importer addon; if import fails, enable it manually in Preferences.
