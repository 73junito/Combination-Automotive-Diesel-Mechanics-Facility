PR Hunk Parser
================

This repository includes a small, dependency-free helper script to fetch a GitHub PR `.patch` and extract `@@` hunk headers for a small set of target files. The outputs are written to `.github/pr_body_with_hunks.md` which lists per-hunk anchors (e.g. `path/to/file.py#L10-L12`).

Run locally (recommended)
-----------------------

From the repository root run:

```bash
python .github/parse_pr_patch_hunks.py --pr 13
```

This fetches `https://patch-diff.githubusercontent.com/raw/73junito/Combination-Automotive-Diesel-Mechanics-Facility/pull/13.patch`, parses hunks for the configured target files and writes `.github/pr_body_with_hunks.md`.

If you prefer to pass a direct patch URL:

```bash
python .github/parse_pr_patch_hunks.py --url 'https://patch-diff.githubusercontent.com/raw/OWNER/REPO/pull/NN.patch'
```

Alternative (git diff, when `origin` is configured locally)
---------------------------------------------------------

If you have the repository checked out and `origin` points to the upstream remote, you can create a focused diff with zero context and parse it instead:

```bash
git fetch origin main
git diff origin/main...HEAD --unified=0 -- \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/assemble_facility.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/write_labels_to_dxf.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/append_legend_to_pdf.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/generate_legend_pdf.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/equipment_bay_mapper.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/replace_labels_with_blocks.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/compute_model_bounds_and_sizes.py \
  Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/print_step_components.py \
  > pr.diff

# then run the parser against the saved diff
python .github/parse_pr_patch_hunks.py --url file://$(pwd)/pr.diff --out .github/pr_body_with_hunks.md
```

Notes
-----
- The script writes GitHub-style anchors `path#Lstart-Lend` which work when pasted into PR bodies.
- The parser is conservative: it only collects hunks for the hard-coded `TARGET_FILES`. Modify the list in the script if you need different files.
