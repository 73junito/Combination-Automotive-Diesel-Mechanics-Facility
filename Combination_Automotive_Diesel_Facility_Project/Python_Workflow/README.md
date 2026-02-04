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
