# PR: Add STEP CAF docs + assemble_facility improvements

This PR adds documentation and enhancements to `assemble_facility.py` to optionally
produce a componentized STEP (STEP CAF) with searchable per-component product names
and metadata, while still producing a unioned STEP/STL for quick visualization.

## Purpose
- Make outputs easier to consume for BIM/workflow tools by writing product `NAME`
  attributes into a single STEP file when OCP/STEPCAF is available.
- Provide a safe fallback (per-part STEP files) when the optional dependency is not
  installed, and preserve unioned exports for fast viewers and bounding-box checks.

## How to test (local)

1. Activate the cadquery environment used for running the scripts:

```powershell
conda activate cadquery
```

2. (Optional but recommended) Install OCP/STEPCAF support so the script can write
   a single componentized STEP with product contexts:

Preferred (mamba):

```powershell
mamba install -c conda-forge ocp pythonocc-core
```

Conda-only alternative:

```powershell
conda install -c conda-forge ocp pythonocc-core
```

3. Run the assembly to produce both componentized and unioned outputs:

```powershell
python Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\assemble_facility.py --export-stl --union
```

4. Expected outputs in `Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/models/`:
- `facility_assembly_components.step` — componentized CAF STEP (if OCP available)
- `components/` — per-part STEP files (created when CAF export is not available)
- `facility_assembly.step` — unioned STEP (created when `--union` used)
- `stl/facility_assembly.stl` — unioned STL (when `--export-stl` used)

5. Verify results:

- Bounding box: the script prints the facility bounding box computed from the STL.
- Component inspection (example):

```powershell
python Combination_Automotive_Diesel_Facility_Project\Python_Workflow\scripts\print_step_components.py "Combination_Automotive_Diesel_Facility_Project\Python_Workflow\outputs\models\facility_assembly_components.step"
```

  - When CAF export succeeded, viewers or `print_step_components.py` should expose
    per-component `name`/`metadata` (e.g. `bay_BLK_E001`, `workbench_BLK_E013`).
  - If CAF export was not available the `components/` folder contains per-part
    STEP files for inspection.

## Notes for reviewers
- The CAF export is optional — scripts still work without `ocp` / `pythonocc-core`.
- The implementation attempts CAF first, then falls back to CadQuery exporters,
  and finally to writing per-part STEP files to ensure reproducible outputs.

## Update PR body with this text
Copy this file into the PR description or use the GitHub CLI to update the PR body:

```bash
gh pr edit 12 --body-file docs/PR_DESCRIPTION_step_caf.md
```
