"""
Generate an engineering legend PDF summarizing assumptions (structural/mech/elec)
and append it to the portfolio PDF, writing `portfolio_final.pdf`.

Reads:
 - outputs/structural_loads.csv
 - outputs/mechanical_services.csv
 - outputs/electrical_loads.csv
 - outputs/equipment_bay_mapping_labeled.csv (for categories)

Writes:
 - outputs/engineering_legend.pdf
 - outputs/portfolio_final.pdf (portfolio_combined_with_legend.pdf + legend)
"""

import csv
import os

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
except ImportError:
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = PdfWriter = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
STRUCT_CSV = os.path.join(OUT, "structural_loads.csv")
MECH_CSV = os.path.join(OUT, "mechanical_services.csv")
ELEC_CSV = os.path.join(OUT, "electrical_loads.csv")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")
PDF_BASE = os.path.join(OUT, "portfolio_combined_with_legend.pdf")
LEGEND_PDF = os.path.join(OUT, "engineering_legend.pdf")
PDF_FINAL = os.path.join(OUT, "portfolio_final.pdf")

# approximate AutoCAD color index -> RGB (0..1)
ACAD_COLOR_RGB = {
    1: (1.0, 0.0, 0.0),
    2: (1.0, 1.0, 0.0),
    3: (0.0, 0.6, 0.0),
    4: (1.0, 0.5, 0.0),
    5: (0.5, 0.0, 0.5),
    6: (0.0, 0.5, 0.0),
    7: (0.8, 0.8, 0.8),
}
# Engineering layer colors mapping
LAYER_COLORS = {
    "STRUCTURAL_ANNOT": 1,  # red
    "MECH_ANNOT": 3,  # green
    "ELEC_SCHEMATIC": 2,  # yellow
}


def read_categories(path):
    cats = []
    if not os.path.exists(path):
        return cats
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            cat = (row.get("Category") or "Other").strip()
            if cat not in cats:
                cats.append(cat)
    return cats


def read_struct(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows.append(row)
    return rows


def read_mech(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows.append(row)
    return rows


def read_elec(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows.append(row)
    return rows


def make_legend_pdf(path, categories, struct_rows, mech_rows, elec_rows):
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not available")
    c = canvas.Canvas(path, pagesize=letter)
    w, h = letter
    margin = 0.75 * inch
    x = margin
    y = h - margin

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Engineering Assumptions & Legend")
    y -= 24

    c.setFont("Helvetica", 10)
    c.drawString(
        x,
        y,
        "This page summarizes preliminary assumptions used for generating engineering annotations. All values are placeholders and require licensed engineer verification.",
    )
    y -= 18

    # Category table (Category -> assumed weight & load)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Category Assumptions")
    y -= 16
    c.setFont("Helvetica", 10)
    # header
    c.drawString(x, y, "Category")
    c.drawString(x + 200, y, "Assumed Weight (lbs)")
    c.drawString(x + 360, y, "Assumed Load (kW)")
    y -= 12

    # small defaults mapping used in scripts (repeat here)
    defaults_weight = {
        "Lift": "2500",
        "Compressor": "500",
        "Diagnostics": "50",
        "Welding": "300",
        "Advanced Diagnostics": "100",
        "Simulator": "800",
        "OEM Tools": "200",
    }
    defaults_load = {
        "Lift": "1.5",
        "Compressor": "7.5",
        "Diagnostics": "0.5",
        "Welding": "5.0",
        "Advanced Diagnostics": "3.5",
        "Simulator": "15.0",
        "OEM Tools": "2.0",
    }

    for cat in categories:
        if y < margin + 80:
            c.showPage()
            y = h - margin
        c.drawString(x, y, cat)
        c.drawString(x + 200, y, defaults_weight.get(cat, "—"))
        c.drawString(x + 360, y, defaults_load.get(cat, "—"))
        y -= 14

    y -= 8
    # Layer color mapping
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Layer Color Mapping")
    y -= 14
    c.setFont("Helvetica", 10)
    for layer, idx in LAYER_COLORS.items():
        if y < margin + 60:
            c.showPage()
            y = h - margin
        rgb = ACAD_COLOR_RGB.get(idx, (0.2, 0.2, 0.2))
        c.setFillColorRGB(*rgb)
        c.rect(x, y - 12, 18, 12, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + 26, y - 2, f"{layer} — Color index {idx}")
        y -= 18

    y -= 6
    # Short CSV summaries (counts)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Summary Counts")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"Structural annotations (rows): {len(struct_rows)}")
    y -= 12
    c.drawString(x, y, f"Mechanical service rows: {len(mech_rows)}")
    y -= 12
    c.drawString(x, y, f"Electrical load rows: {len(elec_rows)}")
    y -= 18

    # Notes
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Notes")
    y -= 14
    c.setFont("Helvetica", 9)
    notes = [
        "• All values are preliminary placeholders for engineering review.",
        "• Structural: slab thickness default = 8 in unless noted in CSV.",
        "• Mechanical: airflow placeholders indicate required review for fume extraction.",
        "• Electrical: per-equipment loads are estimates; verify with manufacturer data.",
        "• Replace placeholder values with licensed-engineer calculations before construction.",
    ]
    for n in notes:
        if y < margin + 40:
            c.showPage()
            y = h - margin
        c.drawString(x, y, n)
        y -= 12

    c.showPage()
    c.save()


def append_pdf(pdf_in, pdf_add, pdf_out):
    if PdfReader is None or PdfWriter is None:
        raise RuntimeError("pypdf not available")
    r1 = PdfReader(pdf_in)
    r2 = PdfReader(pdf_add)
    w = PdfWriter()
    for p in r1.pages:
        w.add_page(p)
    for p in r2.pages:
        w.add_page(p)
    with open(pdf_out, "wb") as fh:
        w.write(fh)


def main():
    cats = read_categories(MAPPING_CSV)
    struct = read_struct(STRUCT_CSV)
    mech = read_mech(MECH_CSV)
    elec = read_elec(ELEC_CSV)

    make_legend_pdf(LEGEND_PDF, cats, struct, mech, elec)
    print("Wrote engineering legend:", LEGEND_PDF)

    if not os.path.exists(PDF_BASE):
        # fallback: append to portfolio_combined.pdf
        base = os.path.join(OUT, "portfolio_combined.pdf")
    else:
        base = PDF_BASE

    append_pdf(base, LEGEND_PDF, PDF_FINAL)
    print("Wrote merged portfolio:", PDF_FINAL)


if __name__ == "__main__":
    main()
