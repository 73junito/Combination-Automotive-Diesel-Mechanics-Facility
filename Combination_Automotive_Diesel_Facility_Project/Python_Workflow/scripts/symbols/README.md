Symbol Library — quick guide

Location: scripts/symbols/

Symbols and recommended layer names:
- HVAC_ExhaustHood.svg  → Layer: `L_HVAC` (use for exhaust hood locations; edit CFM text)
- HVAC_SupplyDiffuser.svg → Layer: `L_HVAC`
- HVAC_ReturnGrille.svg → Layer: `L_HVAC`
- PL_FloorDrain.svg → Layer: `L_Plumbing`
- PL_FloorSink.svg → Layer: `L_Plumbing`
- PL_WaterSupply.svg → Layer: `L_Plumbing`
- PL_CompressedAir.svg → Layer: `L_Plumbing`
- EL_DuplexReceptacle.svg → Layer: `L_Electrical`
- EL_CeilingLight.svg → Layer: `L_Electrical`
- EL_Panelboard.svg → Layer: `L_Electrical`
- GEN_EquipmentClearance.svg → Layer: `L_Floor` or `L_Notes`
- GEN_FlowArrow.svg → Layer: `L_Notes`
- GEN_RefTag.svg → Layer: `L_Notes`

Usage notes:
- All symbols are monochrome stroke-only SVGs centered on origin; scale uniformly when placing in CAD or vector editor.
- For CAD import: convert SVG to DXF or paste as reference geometry on the correct layer.
- Edit the `HVAC_ExhaustHood.svg` text node to fill the CFM value after placing.

If you want, I can:
- Produce a single combined `symbols.svg` file with all symbols grouped by layer for easier import.
- Export DXF versions of each symbol for systems that prefer DXF.

Next: say **review** and point me to a drawing path (PDF/DXF/SVG) and I’ll run a concise gap analysis against the checklist.