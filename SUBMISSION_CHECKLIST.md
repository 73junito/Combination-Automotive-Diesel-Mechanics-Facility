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

Signed-off-by: automation script
