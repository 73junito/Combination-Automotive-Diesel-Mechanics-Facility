#!/usr/bin/env python3
"""
Assemble the Facility Portfolio PDF: cover, master plan image, item lists, totals.

Outputs: outputs/Training_Facility_Drawings_v1.1/PDFs/portfolio_final.pdf
"""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = (
    Path(__file__).resolve().parents[1] / "outputs" / "Training_Facility_Drawings_v1.1"
)
DATA = ROOT / "Data"
PDFS = ROOT / "PDFs"
ASSETS = ROOT / "viewer_assets"
PDFS.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        headers = next(r, [])
        for row in r:
            if not any(cell.strip() for cell in row):
                continue
            rows.append(row)
    return headers, rows


def table_from_csv(path: Path, title: str):
    headers, rows = read_csv_rows(path)
    elems = [Paragraph(title, getSampleStyleSheet()["Heading3"]), Spacer(1, 6)]
    if not headers:
        elems.append(Paragraph("No items found.", getSampleStyleSheet()["Normal"]))
        return elems
    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elems.append(table)
    elems.append(PageBreak())
    return elems


def build_portfolio(out_path: Path):
    doc = SimpleDocTemplate(str(out_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Cover (reuse cover_page.pdf visually by writing a simple cover)
    story.append(Paragraph("Facility Portfolio", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Submitted by: Automation Script", styles["Normal"]))
    story.append(Paragraph("Course: TTED 719 — Spring", styles["Normal"]))
    story.append(
        Paragraph(
            "Polished facility portfolio for administrative review", styles["Normal"]
        )
    )
    story.append(PageBreak())

    # Master plan image
    master_png = ASSETS / "master_plan_300dpi_callout.png"
    if master_png.exists():
        img = Image(
            str(master_png), width=11 * 72, height=8.5 * 72
        )  # full landscape page scaled
        story.append(img)
        story.append(PageBreak())

    # Include discipline snapshots if present (optional)
    for name in ("arch_only.svg", "elec_only.svg", "equip_only.svg"):
        p = ASSETS / name
        if p.exists():
            story.append(Paragraph(name.replace("_", " ").upper(), styles["Heading3"]))
            story.append(
                Paragraph(
                    "See attached SVG in repository viewer assets.", styles["Normal"]
                )
            )
            story.append(Spacer(1, 12))
    story.append(PageBreak())

    # Equipment lists
    story += table_from_csv(DATA / "essential_equipment.csv", "Essential Equipment")
    story += table_from_csv(
        DATA / "nonessential_equipment_with_cost.csv",
        "Non-Essential Equipment (with cost)",
    )
    story += table_from_csv(DATA / "furniture_list.csv", "Furniture List (with cost)")
    story += table_from_csv(
        DATA / "maintenance_and_replacement.csv",
        "Maintenance & Replacement (with cost)",
    )

    # Totals section
    story.append(Paragraph("Total Facility Cost Estimate", styles["Heading2"]))
    data = [
        ["Category", "Subtotal (USD)"],
        ["Essential equipment", "$73,650.00"],
        ["Non-essential equipment", "$28,500.00"],
        ["Furniture", "$35,480.00"],
        ["Maintenance & replacement (line items)", "$30,800.00"],
        ["Combined total (including maintenance items)", "$168,430.00"],
    ]
    table = Table(data, colWidths=[320, 160])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    clar = (
        "For budget planning purposes, a conservative $8,500 maintenance placeholder was used, resulting in a working budget total of $146,130. "
        "Annual maintenance based on explicit line items is estimated at $1,870."
    )
    story.append(Paragraph(clar, styles["Normal"]))

    doc.build(story)
    print("WROTE", out_path)


if __name__ == "__main__":
    out = PDFS / "portfolio_final.pdf"
    build_portfolio(out)
