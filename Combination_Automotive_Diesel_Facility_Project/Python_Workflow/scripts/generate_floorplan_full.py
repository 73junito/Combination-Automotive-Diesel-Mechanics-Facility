from math import cos, radians, sin

import svgwrite

# ---------- Global config ----------

SCALE_FT = 5  # 1 SVG unit = 5 ft (schematic)
WIDTH, HEIGHT = 2200, 1300
MARGIN = 60


# ---------- Helpers ----------


def room(x, y, w, h, label, fill="#f5f5f5", font_size=18):
    dwg.add(
        dwg.rect(insert=(x, y), size=(w, h), fill=fill, stroke="black", stroke_width=2)
    )
    dwg.add(
        dwg.text(
            label, insert=(x + 10, y + h / 2), font_size=f"{font_size}px", fill="black"
        )
    )


def door(x1, y1, x2, y2, color="#424242"):
    dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=color, stroke_width=4))


def interior_wall(x1, y1, x2, y2, color="#9e9e9e"):
    dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke=color, stroke_width=3))


def lift(x, y, w=40, h=60):
    dwg.add(
        dwg.rect(
            insert=(x, y), size=(w, h), fill="#c5e1a5", stroke="black", stroke_width=1
        )
    )
    dwg.add(
        dwg.line(
            start=(x, y + h / 2), end=(x + w, y + h / 2), stroke="black", stroke_width=1
        )
    )


def vehicle(x, y, w=60, h=120, fill="#b0bec5"):
    dwg.add(
        dwg.rect(insert=(x, y), size=(w, h), fill=fill, stroke="black", stroke_width=1)
    )


def equipment_label(x, y, text, color="#000000"):
    dwg.add(dwg.text(text, insert=(x, y), font_size="14px", fill=color))


def grid(step=50, color="#eeeeee"):
    for gx in range(MARGIN, WIDTH - MARGIN, step):
        dwg.add(
            dwg.line(
                start=(gx, MARGIN),
                end=(gx, HEIGHT - MARGIN),
                stroke=color,
                stroke_width=1,
            )
        )
    for gy in range(MARGIN, HEIGHT - MARGIN, step):
        dwg.add(
            dwg.line(
                start=(MARGIN, gy),
                end=(WIDTH - MARGIN, gy),
                stroke=color,
                stroke_width=1,
            )
        )


def arrow(x, y, length, angle_deg, color="#000000"):
    angle = radians(angle_deg)
    x2 = x + length * cos(angle)
    y2 = y - length * sin(angle)
    marker_ref = ARROW_MARKER.get_funciri() if ARROW_MARKER is not None else None
    dwg.add(
        dwg.line(
            start=(x, y),
            end=(x2, y2),
            stroke=color,
            stroke_width=4,
            marker_end=marker_ref,
        )
    )


def create_arrowhead():
    marker = dwg.marker(insert=(5, 5), size=(10, 10), orient="auto", id="arrowhead")
    marker.add(dwg.path(d="M 0 0 L 10 5 L 0 10 z", fill="#000000"))
    dwg.defs.add(marker)
    return marker


def main():
    global dwg, ARROW_MARKER
    dwg = svgwrite.Drawing("facility_floorplan_full.svg", size=(WIDTH, HEIGHT))
    ARROW_MARKER = None

    # ---------- Background + Grid ----------

    dwg.add(dwg.rect(insert=(0, 0), size=(WIDTH, HEIGHT), fill="white"))

    grid(step=50)
    ARROW_MARKER = create_arrowhead()

    # Outer building boundary
    dwg.add(
        dwg.rect(
            insert=(MARGIN, MARGIN),
            size=(WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN),
            fill="none",
            stroke="black",
            stroke_width=4,
        )
    )

    # ---------- Zones ----------

    # Service bay zone (bottom)
    BAY_ZONE_Y = HEIGHT - 380
    BAY_ZONE_H = 260
    dwg.add(
        dwg.rect(
            insert=(MARGIN + 20, BAY_ZONE_Y),
            size=(WIDTH - 2 * MARGIN - 40, BAY_ZONE_H),
            fill="#e3f2fd",
            stroke="none",
        )
    )
    dwg.add(
        dwg.text(
            "SERVICE BAY ZONE",
            insert=(MARGIN + 30, BAY_ZONE_Y - 10),
            font_size="18px",
            fill="#1e88e5",
        )
    )

    # Customer / office zone (top-left)
    CUST_X, CUST_Y, CUST_W, CUST_H = MARGIN + 20, MARGIN + 20, 600, 280
    dwg.add(
        dwg.rect(
            insert=(CUST_X, CUST_Y), size=(CUST_W, CUST_H), fill="#e0f7fa", stroke="none"
        )
    )
    dwg.add(
        dwg.text(
            "CUSTOMER / OFFICE ZONE",
            insert=(CUST_X + 10, CUST_Y - 10),
            font_size="18px",
            fill="#00838f",
        )
    )

    # Parts / storage / fluids zone (top-right)
    PARTS_X, PARTS_Y, PARTS_W, PARTS_H = CUST_X + CUST_W + 40, MARGIN + 20, 750, 280
    dwg.add(
        dwg.rect(
            insert=(PARTS_X, PARTS_Y),
            size=(PARTS_W, PARTS_H),
            fill="#e8f5e9",
            stroke="none",
        )
    )
    dwg.add(
        dwg.text(
            "PARTS / STORAGE / FLUIDS ZONE",
            insert=(PARTS_X + 10, PARTS_Y - 10),
            font_size="18px",
            fill="#2e7d32",
        )
    )

    # ---------- Customer / Office Subrooms ----------

    room(CUST_X + 10, CUST_Y + 10, 280, 130, "CUSTOMER LOUNGE", fill="#b2ebf2")
    room(CUST_X + 310, CUST_Y + 10, 260, 130, "SERVICE WRITE-UP", fill="#ffe0b2")
    room(CUST_X + 10, CUST_Y + 160, 180, 90, "OFFICE", fill="#fff9c4", font_size=16)
    room(
        CUST_X + 210,
        CUST_Y + 160,
        180,
        90,
        "CUSTOMER RESTROOM",
        fill="#f3e5f5",
        font_size=16,
    )
    room(CUST_X + 410, CUST_Y + 160, 160, 90, "BREAK ROOM", fill="#d1c4e9", font_size=16)

    door(CUST_X + 150, CUST_Y + 140, CUST_X + 190, CUST_Y + 140)
    door(CUST_X + 360, CUST_Y + 140, CUST_X + 400, CUST_Y + 140)
    door(CUST_X + 100, CUST_Y + 250, CUST_X + 140, CUST_Y + 250)
    door(CUST_X + 280, CUST_Y + 250, CUST_X + 320, CUST_Y + 250)
    door(CUST_X + 450, CUST_Y + 250, CUST_X + 490, CUST_Y + 250)

    interior_wall(CUST_X + 300, CUST_Y + 10, CUST_X + 300, CUST_Y + 140)
    interior_wall(CUST_X + 10, CUST_Y + 150, CUST_X + 570, CUST_Y + 150)

    # ---------- Parts / Storage / Fluids Subrooms ----------

    room(PARTS_X + 10, PARTS_Y + 10, 260, 130, "PARTS", fill="#c8e6c9")
    room(PARTS_X + 290, PARTS_Y + 10, 260, 130, "STORAGE", fill="#dcedc8")
    room(
        PARTS_X + 10,
        PARTS_Y + 160,
        260,
        90,
        "ELECTRICAL ROOM",
        fill="#f0f4c3",
        font_size=16,
    )
    room(
        PARTS_X + 290, PARTS_Y + 160, 260, 90, "FLUID STORAGE", fill="#f8bbd0", font_size=16
    )

    door(PARTS_X + 140, PARTS_Y + 140, PARTS_X + 180, PARTS_Y + 140)
    door(PARTS_X + 420, PARTS_Y + 140, PARTS_X + 460, PARTS_Y + 140)
    door(PARTS_X + 140, PARTS_Y + 250, PARTS_X + 180, PARTS_Y + 250)
    door(PARTS_X + 420, PARTS_Y + 250, PARTS_X + 460, PARTS_Y + 250)

    interior_wall(PARTS_X + 280, PARTS_Y + 10, PARTS_X + 280, PARTS_Y + 140)
    interior_wall(PARTS_X + 10, PARTS_Y + 150, PARTS_X + 560, PARTS_Y + 150)

    # ---------- Service Bays + Lifts + Vehicles + Equipment ----------

    NUM_BAYS = 16
    BAY_W, BAY_H = 90, 230
    bay_start_x = MARGIN + 40
    bay_y = BAY_ZONE_Y + 25

    for i in range(NUM_BAYS):
        x = bay_start_x + i * (BAY_W + 10)
        dwg.add(
            dwg.rect(
                insert=(x, bay_y),
                size=(BAY_W, BAY_H),
                fill="#e8eaf6",
                stroke="black",
                stroke_width=2,
            )
        )
        dwg.add(
            dwg.text(
                f"BAY {i+1}", insert=(x + 10, bay_y + 20), font_size="14px", fill="black"
            )
        )

        lift_x = x + (BAY_W - 40) / 2
        lift_y = bay_y + 80
        lift(lift_x, lift_y)

        veh_x = x + (BAY_W - 60) / 2
        veh_y = bay_y + 130
        vehicle(veh_x, veh_y)

    equipment_label(bay_start_x, bay_y - 25, "ALIGNMENT RACK (BAY 1)", color="#1b5e20")
    equipment_label(
        bay_start_x + 5 * (BAY_W + 10), bay_y - 25, "TIRE CHANGER (BAY 6)", color="#1b5e20"
    )
    equipment_label(
        bay_start_x + 10 * (BAY_W + 10),
        bay_y - 25,
        "DIAGNOSTIC BAY (BAY 11)",
        color="#1b5e20",
    )

    # ---------- Flow Arrows (vehicles + customers) ----------

    # Vehicle entry arrow (right side)
    arrow(WIDTH - MARGIN - 50, BAY_ZONE_Y + BAY_ZONE_H / 2, 150, 180, color="#d32f2f")
    dwg.add(
        dwg.text(
            "VEHICLE ENTRY",
            insert=(WIDTH - MARGIN - 220, BAY_ZONE_Y + BAY_ZONE_H / 2 - 10),
            font_size="14px",
            fill="#d32f2f",
        )
    )

    # Customer entry arrow (near customer lounge)
    arrow(CUST_X + CUST_W / 2, MARGIN + 10, 120, -90, color="#1976d2")
    dwg.add(
        dwg.text(
            "CUSTOMER ENTRY",
            insert=(CUST_X + CUST_W / 2 - 60, MARGIN + 30),
            font_size="14px",
            fill="#1976d2",
        )
    )

    # Parts flow arrow (from parts to bays)
    arrow(PARTS_X + 100, PARTS_Y + PARTS_H + 20, 150, -90, color="#388e3c")
    dwg.add(
        dwg.text(
            "PARTS TO BAYS",
            insert=(PARTS_X + 40, PARTS_Y + PARTS_H + 40),
            font_size="14px",
            fill="#388e3c",
        )
    )

    # ---------- Exterior Features (parking, landscaping) ----------

    # Parking row (front of building)
    PARK_Y = HEIGHT - MARGIN - 40
    for i in range(10):
        px = MARGIN + 80 + i * 120
        dwg.add(
            dwg.rect(
                insert=(px, PARK_Y),
                size=(80, 30),
                fill="#cfd8dc",
                stroke="black",
                stroke_width=1,
            )
        )
    dwg.add(
        dwg.text(
            "CUSTOMER PARKING",
            insert=(MARGIN + 80, PARK_Y - 10),
            font_size="14px",
            fill="#455a64",
        )
    )

    # Landscaping strip (right side)
    dwg.add(
        dwg.rect(
            insert=(WIDTH - MARGIN - 40, MARGIN + 80),
            size=(30, HEIGHT - 2 * MARGIN - 160),
            fill="#c5e1a5",
            stroke="none",
        )
    )
    dwg.add(
        dwg.text(
            "LANDSCAPING",
            insert=(WIDTH - MARGIN - 150, MARGIN + 90),
            font_size="12px",
            fill="#2e7d32",
        )
    )

    # ---------- Legend / Color Key ----------

    LEG_X, LEG_Y = WIDTH - 520, HEIGHT - 260
    dwg.add(
        dwg.rect(
            insert=(LEG_X, LEG_Y),
            size=(480, 190),
            fill="#fafafa",
            stroke="black",
            stroke_width=2,
        )
    )

    dwg.add(
        dwg.text("LEGEND", insert=(LEG_X + 10, LEG_Y + 25), font_size="18px", fill="black")
    )

    legend_items = [
        ("#e0f7fa", "Customer / Office Zone"),
        ("#e8f5e9", "Parts / Storage / Fluids Zone"),
        ("#e3f2fd", "Service Bay Zone"),
        ("#c5e1a5", "Vehicle Lift"),
        ("#b0bec5", "Vehicle"),
        ("#cfd8dc", "Parking"),
    ]

    for i, (color, label) in enumerate(legend_items):
        ly = LEG_Y + 50 + i * 25
        dwg.add(
            dwg.rect(
                insert=(LEG_X + 10, ly - 15),
                size=(20, 20),
                fill=color,
                stroke="black",
                stroke_width=1,
            )
        )
        dwg.add(dwg.text(label, insert=(LEG_X + 40, ly), font_size="14px", fill="black"))

    dwg.add(
        dwg.text(
            "Arrows: Flow of vehicles, customers, and parts",
            insert=(LEG_X + 10, LEG_Y + 50 + len(legend_items) * 25),
            font_size="14px",
            fill="black",
        )
    )

    # ---------- Title ----------

    dwg.add(
        dwg.text(
            "Combination Automotive Diesel Mechanics Facility - Programmatic Schematic",
            insert=(MARGIN + 20, HEIGHT - 30),
            font_size="24px",
            fill="black",
        )
    )

    dwg.save()
    print("Generated facility_floorplan_full.svg")


if __name__ == "__main__":
    main()
