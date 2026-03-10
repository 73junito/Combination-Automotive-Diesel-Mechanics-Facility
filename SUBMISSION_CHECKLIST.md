## Submission checklist — Training Facility (v1.1)

**Discipline DXFs are exported “views” filtered from the master coordination drawing (`training_facility_plan_layered_mep.dxf`). The master DXF is authoritative (architecture + equipment + MEP layers + labels); discipline-only DXFs are provided for instruction/inspection convenience and include per-file audits (`*.audit.txt`).**

Included files (delivery):

- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/arch_only.dxf` (+ audit)
- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/elec_only.dxf` (+ audit)
- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/mech_only.dxf` (+ audit)
- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/plumb_only.dxf` (+ audit)
- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/fire_only.dxf` (+ audit)
- `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/disciplines/equip_only.dxf` (+ audit)
- Master coordination DXF: `Python_Workflow/outputs/Training_Facility_Drawings_v1.1/training_facility_plan_layered_mep.dxf` (+ audit)

Notes for reviewers:

- The discipline DXFs are filtered copies (views) created from the master DXF; they are intended for convenience and not as the coordination source.
- Labels and full coordination remain in the master DXF. If you require equipment labels to appear in `equip_only.dxf`, request the label-copy pass and I will run it and update the archive.

Quick note for reviewers: SVG previews are provided for browser inspection at `viewer/assets/cad_svg/*.svg` and are embedded interactively in `viewer/index.html` (pan/zoom enabled).

**Mechanical Scope Note:**
The mechanical drawing set is intentionally limited to exhaust ventilation systems supporting automotive instruction bays (Layer: `M-EXHAUST`). General HVAC distribution (supply, return, RTU, ductwork) is not detailed in this facility plan and is assumed to be provided by the base building system. Plumbing utilities (compressed air, drains, oil separation) are shown under `P-AIR`, `P-DRAIN`, and `P-OILSEP` layers.

**Instructor Justification (2 sentences):**
Mechanical scope is intentionally limited to exhaust systems (Layer: M-EXHAUST) to align with automotive instructional safety requirements; full HVAC design is outside the scope of this course project.
This approach prioritizes student health, code-relevant ventilation, and instructional clarity while maintaining realistic facility planning standards.
Signed-off-by: automation script
