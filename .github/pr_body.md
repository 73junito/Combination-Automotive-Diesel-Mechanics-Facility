## Summary

This PR makes the `Python_Workflow` scripts fully **mypy‑clean under Python 3.11**, introduces consistent typing across the mapping and DXF/CadQuery pipelines, and preserves all existing runtime behavior for heavy binary libraries.

---

### What changed
- Added **TypedDicts** (`MappingRow`, `BaySummary`, `MechService`) and applied them across all CSV→mapping consumers.
- Normalized conditional imports for **ezdxf** and **cadquery** using `Optional[ModuleType]` + `TYPE_CHECKING`.
- Introduced targeted `Any` casts in `assemble_facility.py` for OCP/STEP‑CAF runtime‑only symbols to keep static checks separate from runtime behavior.
- Added missing annotations, clarified function signatures, and inserted `None`/union guards throughout the scripts.
- Updated `mypy.ini`:
  - `python_version = 3.11`
  - excluded `outputs/`
  - added targeted `ignore_missing_imports` for heavy binary libs to eliminate external‑stub noise.

---

### Verification
Strict type checking passes cleanly:

```
mypy --check-untyped-defs
Success: no issues found in 48 source files
```

---

### How to reproduce
```
# PowerShell
& .venv-py311\Scripts\Activate.ps1
pre-commit run --all-files
mypy --config-file mypy.ini --check-untyped-defs
```

---

### Notes for reviewers
- External stub packages (e.g., `pandas-stubs`, `types-reportlab`) can be added later; this PR focuses on internal typing correctness.
- New typing patterns introduced:
  - TypedDicts for mapping flows
  - `Optional[ModuleType]` + `TYPE_CHECKING` for conditional imports
  - Targeted `Any` casts for binary‑only runtime symbols

---

### Reviewer highlights
Direct links to the most meaningful changes:

- **assemble_facility.py** — OCP/STEP‑CAF guards and `Any` casts around export paths
- **write_labels_to_dxf.py** — safer `ezdxf` handling and typed label‑placement logic
- **append_legend_to_pdf.py** — typed PDF append flow and corrected `PdfReader` usage
- **generate_legend_pdf.py** — deterministic legend generation with typed rows and categories
- **equipment_bay_mapper.py** — TypedDict‑driven CSV→bay mapping
- **replace_labels_with_blocks.py** — safer DXF block replacement and explicit return types
- **compute_model_bounds_and_sizes.py** — clarified model‑bounds types and DataFrame row typing
- **print_step_components.py** — typed signatures, `None` guards, and explicit return codes

---

If you'd like, I can now help you **add short code snippets** for the top 2–3 hunks to make the review even smoother.
## Summary

This PR makes the `Python_Workflow` scripts fully **mypy‑clean under Python 3.11**, introduces consistent typing across the mapping and DXF/CadQuery pipelines, and preserves all existing runtime behavior for heavy binary libraries.

---

### What changed
- Added **TypedDicts** (`MappingRow`, `BaySummary`, `MechService`) and applied them across all CSV→mapping consumers.
- Normalized conditional imports for **ezdxf** and **cadquery** using `Optional[ModuleType]` + `TYPE_CHECKING`.
- Introduced targeted `Any` casts in `assemble_facility.py` for OCP/STEP‑CAF runtime‑only symbols to keep static checks separate from runtime behavior.
- Added missing annotations, clarified function signatures, and inserted `None`/union guards throughout the scripts.
- Updated `mypy.ini`:
  - `python_version = 3.11`
  - excluded `outputs/`
  - added targeted `ignore_missing_imports` for heavy binary libs to eliminate external‑stub noise.

---

### Verification
Strict type checking passes cleanly:

```
mypy --check-untyped-defs
Success: no issues found in 48 source files
```

---

### How to reproduce
```
# PowerShell
& .venv-py311\Scripts\Activate.ps1
pre-commit run --all-files
mypy --config-file mypy.ini --check-untyped-defs
```

---

### Notes for reviewers
- External stub packages (e.g., `pandas-stubs`, `types-reportlab`) can be added later; this PR focuses on internal typing correctness.
- New typing patterns introduced:
  - TypedDicts for mapping flows
  - `Optional[ModuleType]` + `TYPE_CHECKING` for conditional imports
  - Targeted `Any` casts for binary‑only runtime symbols

---

### Reviewer highlights
Direct links to the most meaningful changes:

- **assemble_facility.py** — OCP/STEP‑CAF guards and `Any` casts around export paths
- **write_labels_to_dxf.py** — safer `ezdxf` handling and typed label‑placement logic
- **append_legend_to_pdf.py** — typed PDF append flow and corrected `PdfReader` usage
- **generate_legend_pdf.py** — deterministic legend generation with typed rows and categories
- **equipment_bay_mapper.py** — TypedDict‑driven CSV→bay mapping
- **replace_labels_with_blocks.py** — safer DXF block replacement and explicit return types
- **compute_model_bounds_and_sizes.py** — clarified model‑bounds types and DataFrame row typing
- **print_step_components.py** — typed signatures, `None` guards, and explicit return codes

---

If you'd like, I can now help you **add short code snippets** for the top 2–3 hunks to make the review even smoother.
**Summary**

This PR makes the Python_Workflow scripts mypy-clean under Python 3.11 and tightens local typing across the codebase. Changes focus on improved static typing while preserving runtime behavior for heavy binary libraries.

**What changed**
- Added local annotations and TypedDicts for mapping flows (MappingRow, BaySummary, MechService).
**Verification**
- Ran mypy --check-untyped-defs inside the Python 3.11 venv (.venv-py311). Final result: Success: no issues found in 48 source files.
**How to reproduce**
1. Activate the provided Python 3.11 venv: source .venv-py311/Scripts/activate (Windows PowerShell: & .venv-py311\Scripts\Activate.ps1).
2. Run formatting/hooks locally: pre-commit run --all-files.
3. Run type checks: mypy --config-file mypy.ini --check-untyped-defs.

**Notes for reviewers**
- I intentionally added ignore_missing_imports for several heavy libraries to keep the focus on internal typing improvements; adding official stubs (e.g., pandas-stubs, 	ypes-reportlab) is a follow-up option.
**Reviewer highlights (6–8 files)**
- Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/assemble_facility.py: Added Any casts and guards for OCP/STEP-CAF code paths to separate runtime binary types from static checks.
If you'd like, I can expand the highlights into direct file links or add short code snippets for the most-reviewer-relevant hunks.
