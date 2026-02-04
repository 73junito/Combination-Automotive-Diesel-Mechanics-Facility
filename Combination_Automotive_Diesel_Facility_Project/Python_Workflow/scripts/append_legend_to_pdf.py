"""
Generate a CAD-style legend (Category -> Color) from
`equipment_bay_mapping_labeled.csv` and append it as a new page
to `portfolio_combined.pdf`, writing `portfolio_combined_with_legend.pdf`.

Tries to use `pypdf` or `PyPDF2` for merging. Uses `reportlab` to build
the legend page.
"""

import csv
import os
from typing import Any, Optional

try:
    from reportlab.lib.pagesizes import \
        letter  # type: ignore[reportMissingImports]
    from reportlab.pdfgen import canvas  # type: ignore[reportMissingImports]
except ImportError:
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True

# annotate pypdf/PyPDF2 reader/writer types for mypy
PdfReader: Optional[Any] = None
PdfWriter: Optional[Any] = None
try:
    # modern pypdf
    from pypdf import \
        PdfReader as _PdfReader  # type: ignore[reportMissingImports]
    from pypdf import PdfWriter as _PdfWriter

    PdfReader = _PdfReader
    PdfWriter = _PdfWriter
except ImportError:
    try:
        from PyPDF2 import \
            PdfReader as _PdfReader2  # type: ignore[reportMissingImports]
        from PyPDF2 import PdfWriter as _PdfWriter2

        PdfReader = _PdfReader2
        PdfWriter = _PdfWriter2
    except ImportError:
        PdfReader = PdfWriter = None

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")
PDF_IN = os.path.join(OUT, "portfolio_combined.pdf")
LEGEND_PDF = os.path.join(OUT, "legend_page.pdf")
PDF_OUT = os.path.join(OUT, "portfolio_combined_with_legend.pdf")

# approximate AutoCAD color index -> RGB (0..1)
ACAD_COLOR_RGB = {
    1: (1.0, 0.0, 0.0),
    2: (1.0, 1.0, 0.0),
    3: (0.0, 0.0, 1.0),
    4: (1.0, 0.5, 0.0),
    5: (0.5, 0.0, 0.5),
    6: (0.0, 0.5, 0.0),
    7: (0.8, 0.8, 0.8),
    8: (0.0, 1.0, 1.0),
    9: (1.0, 0.0, 1.0),
    10: (0.6, 0.3, 0.0),
}
COLOR_PALETTE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def load_categories(csv_path):
    """Load categories from CSV at ``csv_path`` and return unique list."""
    cats = []
    if not os.path.exists(csv_path):
        return cats
    with open(csv_path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            cat = (row.get("Category") or "Other").strip()
            if cat not in cats:
                cats.append(cat)
    return cats


def build_color_map(categories):
    """Return a mapping of category -> AutoCAD color index."""
    cmap = {}
    for i, cat in enumerate(categories):
        idx = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        cmap[cat] = idx
    return cmap


def make_legend_pdf(legend_pdf_path, categories, color_map):
    """Create a PDF file at ``legend_pdf_path`` listing ``categories``.

    Uses ``color_map`` to draw color swatches.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not available")
    c = canvas.Canvas(legend_pdf_path, pagesize=letter)
    _, height = letter
    margin = 72
    x = margin
    y = height - margin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Legend — Equipment Category and Color")
    y -= 30
    c.setFont("Helvetica", 11)
    for cat in categories:
        color_idx = color_map.get(cat, 7)
        rgb = ACAD_COLOR_RGB.get(int(color_idx), (0.2, 0.2, 0.2))
        c.setFillColorRGB(*rgb)
        # draw swatch
        sw = 18
        c.rect(x, y - sw + 4, sw, sw, fill=1, stroke=0)
        # label
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + sw + 10, y, f"{cat}  (Color {color_idx})")
        y -= sw + 8
        if y < margin + 40:
            c.showPage()
            y = height - margin
    c.save()


def append_pdf(pdf_in, legend_pdf, pdf_out):
    """Append pages from ``legend_pdf`` onto ``pdf_in`` and write ``pdf_out``."""
    if PdfReader is None or PdfWriter is None:
        raise RuntimeError("pypdf/PyPDF2 not available for merging")
    reader_main = PdfReader(pdf_in)
    reader_legend = PdfReader(legend_pdf)
    writer = PdfWriter()
    for p in reader_main.pages:
        writer.add_page(p)
    for p in reader_legend.pages:
        writer.add_page(p)
    with open(pdf_out, "wb") as fh:
        writer.write(fh)


def main():
    """Main entrypoint: generate legend and append it to portfolio PDF."""
    cats = load_categories(MAPPING_CSV)
    if not cats:
        print("No categories found in", MAPPING_CSV)
        return
    cmap = build_color_map(cats)
    print("Categories:", cats)
    print("Color map:", cmap)
    make_legend_pdf(LEGEND_PDF, cats, cmap)
    print("Legend PDF written to", LEGEND_PDF)
    append_pdf(PDF_IN, LEGEND_PDF, PDF_OUT)
    print("Merged PDF written to", PDF_OUT)


if __name__ == "__main__":
    main()
