Python Workflow for Combination Automotive/Diesel Facility

Setup

1. Create and activate the virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1. VS Code will pick up the interpreter at `.venv/Scripts/python.exe`.
2. The CadQuery source is included in the workspace at `CadQuery 2.6.1 source code` and is added to `python.analysis.extraPaths` in `.vscode/settings.json` for completion.

Notes

- If you prefer to install `cadquery` from PyPI, uncomment or add `cadquery==2.6.1` to `requirements.txt`.
- To run scripts, use the workspace interpreter explicitly if needed:

```powershell
.\.venv\Scripts\python.exe scripts\your_script.py
```

## Optional: Componentized STEP export (STEP CAF)

The assembly scripts can optionally write a componentized STEP file with per-component product
names and metadata (useful for BIM workflows and searchable product attributes). This requires
OCP / pythonocc (`STEPCAFControl_Writer`) in the CadQuery runtime.

Install into your CadQuery environment (preferred via `mamba`):

```powershell
conda activate cadquery
mamba install -c conda-forge ocp pythonocc-core
```

Or using `conda` only:

```powershell
conda activate cadquery
conda install -c conda-forge ocp pythonocc-core
```

Once installed, run the assembly script. It will attempt a STEP CAF export (componentized
STEP) first and fall back to per-part STEP files if the CAF writer is unavailable:

```powershell
conda activate cadquery
python Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\assemble_facility.py --export-stl --union
```

Outputs written to `Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/models/`:
- `facility_assembly_components.step` (componentized CAF STEP, when available)
- `components/` (per-part STEP files if CAF export fails)
- `facility_assembly.step` (unioned STEP, when `--union` used)
- `stl/facility_assembly.stl` (unioned STL)

Note: `ocp` / `pythonocc-core` is an optional runtime dependency only required to produce a
single componentized STEP with product names. The scripts will still run and produce unioned
and per-part STEP files without it.

## Testing the cleanup notification payload (dry-run)

A small helper script is provided to build and preview the Slack Blocks payload that the
cleanup workflow sends when it prunes draft releases. It is useful for validating formatting
and asset link rendering without touching production webhooks.

- Script: Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/send_cleanup_test_payload.py
- Purpose: produce a JSON payload that mirrors the workflow's Slack Blocks and optionally POST it to a webhook.

Quick usage:

Print the sample payload and save to `docs/cleanup_test_payload.json`:

```powershell
python Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\send_cleanup_test_payload.py
```

Post the sample payload to a test webhook (e.g. webhook.site or a Slack Incoming Webhook):

```powershell
python Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\send_cleanup_test_payload.py --webhook 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
```

Options:
- `--deleted N` : number of sample deleted releases to include (default 2)
- `--max-assets N` : max assets to show per release in the sample (default 3)
- `--output PATH` : write payload JSON to a file (default `docs/cleanup_test_payload.json`)

This README entry documents the test harness so future maintainers can validate the
cleanup Blocks formatting and threshold behavior before they run the workflow against
real webhooks.

## Plan Previews

Quick previews of the generated facility plans are embedded below. These use the
programmatically produced SVGs so they render directly on GitHub and stay in sync
with the source scripts.

- **Electrical plan**

	![Electrical Plan](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/facility_electrical_plan.svg)

- **HVAC plan**

	![HVAC Plan](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/facility_hvac_plan.svg)

- **Plumbing plan**

	![Plumbing Plan](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/facility_plumbing_plan.svg)

### PNG thumbnails (CI-generated)

The PNG thumbnails below are produced by the automated CI job (`.github/workflows/render-plans-to-png.yml`) and are stored under `Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/thumbs` when present. If they are not available in-tree you can download them from the workflow run artifacts (`facility-plan-thumbs`).

- **Electrical (thumbnail)**  
	![Electrical Thumb](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/thumbs/facility_electrical_plan.thumb.png)

- **HVAC (thumbnail)**  
	![HVAC Thumb](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/thumbs/facility_hvac_plan.thumb.png)

- **Plumbing (thumbnail)**  
	![Plumbing Thumb](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/thumbs/facility_plumbing_plan.thumb.png)

- **Exterior elevation (thumbnail)**  
	![Exterior Thumb](Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/thumbs/facility_exterior_elevation.thumb.png)

Note: the repository includes a CI workflow that converts these SVGs to PNGs and thumbnail images and uploads them as workflow artifacts. See `.github/workflows/render-plans-to-png.yml` — artifacts are uploaded as `facility-plan-pngs` and `facility-plan-thumbs` on each run.

## Blender 3D model (programmatic)

A Blender script is provided to generate a base 3D model of the facility from the programmatic dimensions. The script is:

- `Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/build_facility_3d.py`

Run it inside Blender (recommended) or headless on CI runners that have Blender installed. Example command (adjust Blender executable path as needed):

```bash
# Interactive (open Blender and run script from Text Editor or run via command line)
blender --python Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/build_facility_3d.py

# Headless (background) render-only run
blender --background --python Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/build_facility_3d.py --render-output //renders/frame_ -noaudio --render-frame 1
```

The script creates a simple, parameterized building shell, service bays, parking, and basic materials. Use Blender to refine materials, add interiors, or export to FBX/GLTF/USD as needed.
