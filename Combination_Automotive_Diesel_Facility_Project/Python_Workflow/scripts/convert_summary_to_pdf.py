"""Convert the executive summary TXT to a simple PDF using reportlab.

Usage: run from repo root with virtualenv active.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from textwrap import wrap


def txt_to_pdf(txt_path, pdf_path, page_size=letter, margin=72):
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    c = canvas.Canvas(pdf_path, pagesize=page_size)
    width, height = page_size
    x = margin
    y = height - margin
    max_width = width - 2 * margin
    # choose a readable font and size
    c.setFont("Helvetica", 10)
    leading = 12

    for raw in lines:
        if raw.strip() == "":
            y -= leading
            if y < margin:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - margin
            continue
        # wrap long lines
        wrapped = wrap(raw, width=95)
        for wline in wrapped:
            c.drawString(x, y, wline)
            y -= leading
            if y < margin:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - margin

    c.save()


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
    txt = os.path.join(base, "Executive_Summary_v1.1.txt")
    pdf = os.path.join(base, "Executive_Summary_v1.1.pdf")
    if not os.path.exists(txt):
        print(f"Source TXT not found: {txt}")
        return 1
    txt_to_pdf(txt, pdf)
    print(f"Created PDF: {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
