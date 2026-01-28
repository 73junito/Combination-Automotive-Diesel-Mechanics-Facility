# Facility Layout — Annotation & Edit Checklist (US customary units)

File: `portfolio_final.pdf` (main sheet)
Source DXF: `facility_layout_engineering.dxf`

---

## 1) Layers to add / fix
- Add layer `FLOOR` and move floor polylines from `STRUCTURAL_ANNOT` to `FLOOR` (non-destructive copy).
- Verify the following layers exist and are used consistently:
  - `WALLS`, `FLOOR`, `EQUIPMENT`, `EQUIP_LABELS`, `ELECTRICAL`, `HVAC`, `PLUMBING`, `AIR_GAS`, `AUTO_BAYS`, `DIESEL_BAYS`, `TEXT_LABELS`, `TRAFFIC_FLOW`, `DIMENSIONS`, `TITLE_BLOCK`.
- Set layer colors/lineweights: walls (heaviest), equipment (medium), annotations/labels (light).

## 2) Title block fields to populate (vector text on `TITLE_BLOCK`)
- Project Name: Combination Automotive & Diesel Facility
- Author: <Student Name>
- Sheet Number: A1 — Facility Layout
- Date: 2026-01-26
- Revision: Rev 0 — Issued for Review
- Scale text: "Scale: 1/8\" = 1'-0\"" (or chosen US architectural scale)

Action: Replace any rasterized title-block content with selectable text entities.

## 3) North arrow & scale bar
- Add a vector north arrow (label "N") near the title block on `TEXT_LABELS` or `GRAPHICS`.
- Add a graphic scale bar sized for the sheet and the chosen scale. Example: show ticks for 0', 25', 50' and label "Scale: 1/8\" = 1'-0\"" on `TITLE_BLOCK`.

## 4) Key dimensions to add (put dims on `DIMENSIONS`, text readable at print scale)
Add at least 3–5 dimensions in US units (feet & inches):
- Overall building width — e.g., `120'-0"` (exterior wall to exterior wall).
- Bay depth (typical AUTO bay) — e.g., `24'-0"` (face-of-bay to rear wall).
- Main aisle width (clearance between equipment rows) — e.g., `12'-0"`.
- Primary exit door clearances (one or two critical doors) — e.g., `3'-0"`.

Notes: Use architectural dimension style (leader or aligned dims) and consistent text height (readable at plotted scale).

## 5) Discipline labels to add (exact sample text + target layer)
Place these as vector text on the listed layers; include short capacity/qty where applicable.

- `ELECTRICAL`:
  - "Panel LP-1 — 120/208V 3PH (East wall)"
  - "Receptacle @ lifts — 120V 20A" (note: "@ lifts" means at each lift location)
- `HVAC`:
  - "Diesel exhaust hood — 1,500 CFM"  
  - "Lift area supply — 500 CFM"
- `PLUMBING`:
  - "Floor drain → trench drain (slope w)"  
  - "Service sink — cold water"
- `AIR_GAS`:
  - "Compressed air drop @ each bay — 100 PSI"
- `EQUIP_LABELS` (for key equipment, show qty & capacity):
  - "Two-post lift — 10 ea — 2,500 lb"  
  - "Air compressor (50 CFM) — 2 ea — 7.5 kW"
- `AUTO_BAYS` / `DIESEL_BAYS`:
  - Label bays: "AUTO BAY 1", "AUTO BAY 2", "DIESEL BAY 1", etc.

Place at least 3 labeled items per discipline on the main sheet.

## 6) Legend entries to confirm (text, visible, exact layer names)
Legend must be selectable text and include symbol → name → layer. Example entries:
- "Exhaust Hood — HVAC (HVAC)"
- "Floor Drain — Plumbing (PLUMBING)"
- "Air Drop — Air/Gas (AIR_GAS)"
- "Lift — Equipment (EQUIPMENT)"

Action: Ensure legend entries spell the layer names exactly as used in the DXF.

## 7) PDF export checks (verify after edits)
- Export PDF with selectable text (no rasterized text in title block or legend).
- Embed fonts or use system fonts to keep text selectable.
- If your CAD export supports PDF layers (OCG), enable them so reviewers can toggle layers.
- Quick verification steps:
  - Select and copy the Project Name from the PDF to confirm text is selectable.
  - Toggle a discipline layer (if PDF OCG used) and confirm its annotations hide/show.

## 8) Visual/manual confirmations (final QA before submission)
- Toggle `ELECTRICAL`, `HVAC`, `PLUMBING`, `AIR_GAS` and confirm only that discipline's annotations are visible.
- Zoom to print scale and confirm text legibility and no overlapping labels.
- Confirm at least 3 labeled items per discipline.

## 9) Minimal DXF edit commands (for manual CAD work)
- Create layer `FLOOR` (properties: Continuous, color X, weight Y). Copy floor geometry from `STRUCTURAL_ANNOT` to `FLOOR`.
- Create `DIMENSIONS` layer; run `DIM` to create building width, bay depth, aisle width dims.
- Replace title block text with vector text on `TITLE_BLOCK`.
- Add north arrow block; insert & rotate to true north, place on `TEXT_LABELS`.
- Add legend text entries (update to include layer names precisely).

---

If you want, I can now:
- 1) Save this checklist to `Python_Workflow/outputs/facility_layout_annotation_list.md` (already created), or
- 2) Attempt non-destructive automated edits to the DXF (create `FLOOR`, add text strings, add dims) and write a draft DXF for your review — this will modify geometry programmatically and I will not overwrite originals unless you confirm.

Which next action do you want? (1 = manual checklist only; 2 = apply scripted DXF edits draft)