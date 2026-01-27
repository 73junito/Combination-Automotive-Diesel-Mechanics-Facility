Quick Start: DXF → SVG → Blender → PNG

Prerequisites
- Install Inkscape (https://inkscape.org) and ensure `inkscape` is on PATH or note its full executable path.
- Install Blender (https://blender.org) and ensure `blender` is on PATH or note its full executable path.

1) Prepare outputs folder
```powershell
New-Item -ItemType Directory -Path ".\Python_Workflow\scripts\outputs" -Force
```

2) Convert DXF → SVG
```powershell
.
\Python_Workflow\scripts\convert_dxf_to_svg.ps1 \
  -InputPath ".\Drawings\CAD\layout.dxf" \
  -OutputPath ".\Python_Workflow\scripts\outputs\layout.svg"
```
If Inkscape is not on PATH, add `-InkscapePath "C:\Program Files\Inkscape\bin\inkscape.exe"`.

3) Run full pipeline (convert + optional Blender render)
```powershell
.
\Python_Workflow\scripts\run_pipeline.ps1 \
  -DxfPath ".\Drawings\CAD\layout.dxf" \
  -OutputDir ".\Python_Workflow\scripts\outputs" \
  -ResX 3840 -ResY 2160 -ApplyScale
```
If Blender isn't on PATH, pass `-BlenderPath "C:\Program Files\Blender Foundation\Blender\blender.exe"`.

4) Verify outputs
- SVG: `Python_Workflow\scripts\outputs\<basename>.svg`
- PNG render: `Python_Workflow\scripts\outputs\<basename>.png`

5) Optional: add PNG to submission ZIP without modifying originals
```powershell
Compress-Archive -Path ".\Python_Workflow\scripts\outputs\layout.png" -Update -DestinationPath ".\submission\student_submission.zip"
```
Or create a separate bonus ZIP:
```powershell
Compress-Archive -Path ".\Python_Workflow\scripts\outputs\layout.png" -DestinationPath ".\Python_Workflow\scripts\outputs\layout_bonus_view.zip" -Force
```

Troubleshooting
- Missing/very thin lines: open the SVG in Inkscape and inspect `Object → Fill and Stroke` to increase stroke widths; re-export if needed.
- Blender SVG import error: enable the add-on in Blender GUI `Edit → Preferences → Add-ons → Import-Export: Scalable Vector Graphics (SVG)` and re-run.
- Object scale/position issues: re-run `run_pipeline.ps1` with `-Scale <value>` or toggle `-ApplyScale`.

Notes & Guardrails
- This workflow is for visualization/reference only. Do not treat the Blender scene as a CAD-accurate source for fabrication.
- The scripts produce outputs in `scripts/outputs` to avoid overwriting original submission files.

If you want, I can also add a single-click PowerShell script that zips the SVG+PNG into a `bonus_view.zip` and prints a short checklist for submission. Say the word and I’ll add it.