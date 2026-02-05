# TTED 719 — Repo → Learning Outcomes (one page)

Purpose
- Map repo artifacts to TTED 719 learning outcomes and provide an instructor-ready summary (one page).

Key instructor-facing outcomes (evidence-focused)
- Demonstrates facility planning competency — Documents floorplans, CAD exports, and scripted layout assembly that instructors can inspect and reuse.
- Implements safety & compliance practices — Produces inspection-ready PDFs and consolidated safety checklists for quick review.
- Integrates instructional and industry requirements — Generates instructor handouts and slide-ready assets from source CSV/XLSX.
- Documents cost and resource analysis — Produces reproducible cost calculations and printable cost summaries from equipment lists.
- Supports assessment & reproducibility — Provides typed scripts, CI checks, and run steps so outputs are traceable and repeatable.

Mapping: TTED 719 Topics → Repo artifacts (evidence)
- Facilities & Layouts: `Drawings/CAD` (floorplans), DXF exports, and `Python_Workflow/scripts` (assemble, generate_legend, append_legend) — demonstrates repeatable layout generation.
- Safety & Compliance: `Documentation/` and TTED PDFs plus generated inspection reports — demonstrates documented safety review artifacts.
- Lighting & Environmental Design: `Python_Workflow/TTED 719` extracts and charts (lighting/footcandle) — demonstrates application of lighting recommendations into plans.
- Equipment & Costing: Spreadsheets and scripts that produce planning PDFs from CSV/XLSX — demonstrates traceable cost and equipment summaries.
- Instructional Planning: Syllabi, slides, and automation to create instructor-facing handouts — demonstrates conversion of source data into teaching materials.

Added value (how this repo exceeds basic TTED 719 expectations)
- Executable workflows: Scripts turn static examples into repeatable deliverables (DXF, PDF, cost reports).
- Traceability: Strong typing, CI checks, and documented commands make outputs auditable and reproducible.
- Teaching resource: The codebase is usable as a lab exercise for CAD automation, data-driven planning, and reproducible instructional artifacts.

How instructors can use this file (quick actions)
- Regenerate deliverables: Run `Python_Workflow/scripts` to refresh PDFs and drawings after edits.
- Produce an index: Run `tted719_extract.py` to create an instructor index of example files.
- Cite this page: Use this one-page mapping as a compact justification in proposals or accreditation packets.

Status
- `TTED719_mapping.pdf` generated and committed to this branch as a printable one-page handout.

---

