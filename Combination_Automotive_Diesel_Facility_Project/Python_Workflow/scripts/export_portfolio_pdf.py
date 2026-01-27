"""
Export combined portfolio to a single PDF:
- Creates a schematic thumbnail from DXF bay bounding boxes and mapping
- Assembles PDF with: title page + thumbnail, Bay Summary table page, Cost Chart page
- Uses reportlab for PDF, matplotlib for drawing thumbnail and table image
"""

import os
import io
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd

try:
    import ezdxf
except ImportError:
    ezdxf = None

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_LABELED = os.path.join(OUT, "facility_layout_labeled.dxf")
PORTFOLIO_XLSX = os.path.join(OUT, "portfolio_equipment_by_bay.xlsx")
CHART_PNG = os.path.join(OUT, "totalcost_per_bay.png")
THUMB_PNG = os.path.join(OUT, "facility_layout_thumbnail.png")
PDF_OUT = os.path.join(OUT, "portfolio_combined.pdf")
MAPPING_CSV = os.path.join(OUT, "equipment_bay_mapping_labeled.csv")


def make_thumbnail(dxf_path, mapping_csv, out_png):
    if ezdxf is None:
        raise RuntimeError("ezdxf is required to read DXF")
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    # collect bay rectangles
    rects = []
    for e in msp:
        etype = e.dxftype()
        layer = getattr(e.dxf, "layer", "")
        if etype in ("LWPOLYLINE", "POLYLINE") and layer in ("AUTO_BAYS", "DIESEL_BAYS"):
            try:
                pts = (
                    list(e.get_points())
                    if hasattr(e, "get_points")
                    else [tuple(v) for v in e.vertices()]
                )
            except AttributeError:
                pts = [tuple(v) for v in e.vertices()]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
            rects.append({"layer": layer, "minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy})
    if not rects:
        raise RuntimeError("No bay rectangles found in DXF")
    # compute extents
    minx = min(r["minx"] for r in rects)
    miny = min(r["miny"] for r in rects)
    maxx = max(r["maxx"] for r in rects)
    maxy = max(r["maxy"] for r in rects)
    width = maxx - minx
    height = maxy - miny
    fig_w = 10
    fig_h = max(4, fig_w * (height / width))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_aspect("equal")
    ax.set_axis_off()
    # draw rectangles
    for r in rects:
        x = r["minx"] - minx
        y = r["miny"] - miny
        w = r["maxx"] - r["minx"]
        h = r["maxy"] - r["miny"]
        color = "#a6cee3" if r["layer"] == "AUTO_BAYS" else "#b2df8a"
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="k", alpha=0.6)
        ax.add_patch(rect)
    # overlay labels from mapping
    if os.path.exists(mapping_csv):
        df = pd.read_csv(mapping_csv)
        for _, row in df.iterrows():
            try:
                cx = float(row.get("BayCX")) - minx
                cy = float(row.get("BayCY")) - miny
                label = f"{row.get('EquipID')}"
                ax.text(cx, cy, label, fontsize=6, ha="center", va="center")
            except (TypeError, ValueError):
                pass
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


def build_pdf(thumbnail, excel_path, chart_path, pdf_out):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_out, pagesize=letter)
    story = []
    title = Paragraph("Combination Automotive & Diesel Facility Portfolio", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))
    # thumbnail
    if os.path.exists(thumbnail):
        story.append(Paragraph("Facility Layout (schematic)", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(RLImage(thumbnail, width=480, height=300))
        story.append(Spacer(1, 12))
    # Bay Summary table (load from Excel)
    if os.path.exists(excel_path):
        summary = pd.read_excel(excel_path, sheet_name="Bay Summary")
        story.append(Paragraph("Bay Summary", styles["Heading2"]))
        story.append(Spacer(1, 6))
        # render small table as image via matplotlib for consistent layout
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.axis("off")
        ax.table(
            cellText=summary.head(20).values,
            colLabels=summary.columns,
            loc="center",
            cellLoc="center",
        )
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf)
        img_path = os.path.join(OUT, "bay_summary_preview.png")
        img.save(img_path)
        story.append(RLImage(img_path, width=480, height=240))
        story.append(Spacer(1, 12))
    # Cost chart
    if os.path.exists(chart_path):
        story.append(Paragraph("Total Cost per Bay", styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(RLImage(chart_path, width=480, height=300))
    doc.build(story)
    return pdf_out


def main():
    thumb = make_thumbnail(DXF_LABELED, MAPPING_CSV, THUMB_PNG)
    pdf = build_pdf(thumb, PORTFOLIO_XLSX, CHART_PNG, PDF_OUT)
    print("Wrote PDF:", pdf)


if __name__ == "__main__":
    main()
