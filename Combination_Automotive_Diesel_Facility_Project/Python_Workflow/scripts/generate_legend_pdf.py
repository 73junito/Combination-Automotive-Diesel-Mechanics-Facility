from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os


def build_legend(output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Drawing Legend & Layer Guide", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Project: Combination Automotive Diesel Mechanics Facility",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Drawing set files:", styles["Heading3"]))
    files = [
        "ARCH_Plan.dxf",
        "ELEC_Plan.dxf",
        "PLUMB_Plan.dxf",
        "MECH_Plan.dxf",
        "EQUIP_Plan.dxf",
        "FURN_Plan.dxf",
    ]
    for f in files:
        story.append(Paragraph(f, styles["Bullet"]))
    story.append(Spacer(1, 18))

    story.append(
        Paragraph("Layer & Symbol Legend (coordination only)", styles["Heading2"])
    )
    story.append(Spacer(1, 6))

    # Table header
    data = [["Layer", "Symbol / Type", "Represents", "Notes"]]

    rows = [
        ("A-WALL-EXT", "Wall ext", "Exterior walls", "Architectural"),
        ("A-WALL-INT", "Wall int", "Interior partitions", "Architectural"),
        ("A-DOOR", "Door", "Doors and openings", "Architectural"),
        ("A-GRID", "Grid", "Structural grid", "Architectural"),
        ("E-LIGHT-FIX", "Lighting", "Light fixtures", "Coord only"),
        ("E-POWER-OUT", "Power drop", "120/240V receptacles", "Location only"),
        (
            "E-POWER-3PH",
            "3-Phase power",
            "208/480V drops for lifts/chargers",
            "Location only",
        ),
        ("E-PANEL", "Panel", "Electrical panel placeholder", "Coord only"),
        ("E-EMERG", "EMO", "Emergency shutoff / EMO", "Coord only"),
        ("E-DATA", "Data", "Network / instructor stations", "Coord only"),
        ("P-WATER", "Pipe", "Cold / hot water", "Coord only"),
        ("P-DRAIN", "Drain", "Floor drains", "Coord only"),
        ("P-AIR", "Air drop", "Compressed air drops", "Coord only"),
        ("P-OILSEP", "Conn", "Oil-water separator connection", "Coord only"),
        ("M-AHU", "AHU", "Air handling unit", "Coord only"),
        ("M-EXHAUST", "Exhaust", "Vehicle exhaust capture points", "Coord only"),
        ("M-VENT", "Vent", "General ventilation zones", "Coord only"),
        ("EQ-LIFT", "Lift", "Vehicle lift footprint", "Spec lift type in notes"),
        ("EQ-ALIGN", "Alignment rack", "Wheel alignment equipment", "Coord only"),
        ("EQ-CHARGE", "EV charger", "EV charging station", "Location only"),
        ("EQ-TOOLBOX", "Toolbox", "Rolling toolboxes", "Furniture/equipment"),
        ("EQ-WASH", "Wash bay", "Vehicle wash / detail bay", "Coord only"),
        ("EQ-COMP", "Compressor", "Air compressor room", "Coord only"),
        ("EQ-FLAM", "Cabinet", "Flammable storage cabinet", "Per code: locate per AHJ"),
        ("EQ-BATT", "Cabinet", "Battery storage cabinet", "Per code"),
        ("FURN-DESK", "Desk", "Student / instructor desks", "Furniture"),
        ("FURN-TABLE", "Table", "Work tables / high-top", "Furniture"),
        ("FURN-CHAIR", "Chair", "Stools / seating", "Furniture"),
        ("FURN-LOCKER", "Locker", "Student lockers", "Furniture"),
        ("FURN-STOR", "Storage", "Tool storage walls / cabinets", "Furniture"),
        ("FURN-BOARD", "Board", "Whiteboard / display wall", "Furniture"),
    ]

    for r in rows:
        data.append(list(r))

    table = Table(data, colWidths=[110, 110, 160, 120])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Notes:", styles["Heading3"]))
    story.append(
        Paragraph(
            "This drawing set is coordination-level only. MEP and structural systems\nare placeholders for coordination and must be engineered and sized by licensed professionals.",
            styles["Normal"],
        )
    )

    doc.build(story)


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_pdf = os.path.join(out_dir, "Drawing_Legend_and_Layer_Guide.pdf")
    build_legend(out_pdf)
    print(f"Generated legend PDF: {out_pdf}")
