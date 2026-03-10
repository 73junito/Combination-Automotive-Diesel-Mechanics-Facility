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