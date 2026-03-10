import svgwrite

WIDTH, HEIGHT = 2200, 1300
MARGIN = 60

# ---------- Shared helpers ----------


def base_drawing(filename):
    dwg = svgwrite.Drawing(filename, size=(WIDTH, HEIGHT))
    dwg.add(dwg.rect(insert=(0, 0), size=(WIDTH, HEIGHT), fill="white"))
    # Outer building
    dwg.add(
        dwg.rect(
            insert=(MARGIN, MARGIN),
            size=(WIDTH - 2 * MARGIN, HEIGHT - 2 * MARGIN),
            fill="none",
            stroke="black",
            stroke_width=4,
        )
    )
    # Service bay zone
    bay_zone_y = HEIGHT - 380
    bay_zone_h = 260
    dwg.add(
        dwg.rect(
            insert=(MARGIN + 20, bay_zone_y),
            size=(WIDTH - 2 * MARGIN - 40, bay_zone_h),
            fill="#f5f5f5",
            stroke="none",
        )
    )
    # Bays
    num_bays = 16
    bay_w, bay_h = 90, 230
    bay_start_x = MARGIN + 40
    bay_y = bay_zone_y + 25
    for i in range(num_bays):
        x = bay_start_x + i * (bay_w + 10)
        dwg.add(
            dwg.rect(
                insert=(x, bay_y),
                size=(bay_w, bay_h),
                fill="none",
                stroke="black",
                stroke_width=1,
            )
        )
        dwg.add(dwg.text(f"BAY {i+1}", insert=(x + 10, bay_y + 20), font_size="12px"))
    # Customer / office block
    cust_x, cust_y, cust_w, cust_h = MARGIN + 20, MARGIN + 20, 600, 280
    dwg.add(
        dwg.rect(
            insert=(cust_x, cust_y),
            size=(cust_w, cust_h),
            fill="none",
            stroke="black",
            stroke_width=2,
        )
    )
    dwg.add(
        dwg.text(
            "CUSTOMER / OFFICE ZONE",
            insert=(cust_x + 10, cust_y - 10),
            font_size="16px",
        )
    )
    # Parts / storage / fluids block
    parts_x, parts_y, parts_w, parts_h = cust_x + cust_w + 40, MARGIN + 20, 750, 280
    dwg.add(
        dwg.rect(
            insert=(parts_x, parts_y),
            size=(parts_w, parts_h),
            fill="none",
            stroke="black",
            stroke_width=2,
        )
    )
    dwg.add(
        dwg.text(
            "PARTS / STORAGE / FLUIDS ZONE",
            insert=(parts_x + 10, parts_y - 10),
            font_size="16px",
        )
    )
    return (
        dwg,
        (cust_x, cust_y, cust_w, cust_h),
        (parts_x, parts_y, parts_w, parts_h),
        (bay_start_x, bay_y, bay_w, bay_h, num_bays),
    )


# ---------- Electrical Plan ----------


def create_electrical_plan():
    dwg, cust, parts, bays = base_drawing("facility_electrical_plan.svg")
    cust_x, cust_y, cust_w, cust_h = cust
    parts_x, parts_y, parts_w, parts_h = parts
    bay_start_x, bay_y, bay_w, bay_h, num_bays = bays

    # Panel boards in parts/electrical area
    panel_x = parts_x + 40
    panel_y = parts_y + 60
    for i in range(3):
        y = panel_y + i * 80
        dwg.add(
            dwg.rect(
                insert=(panel_x, y),
                size=(40, 60),
                fill="#fff3e0",
                stroke="black",
                stroke_width=1,
            )
        )
        dwg.add(dwg.text(f"PNL-{i+1}", insert=(panel_x + 5, y + 35), font_size="10px"))

    # Receptacles along customer wall
    for i in range(6):
        x = cust_x + 40 + i * 90
        y = cust_y + cust_h - 10
        dwg.add(
            dwg.circle(
                center=(x, y), r=6, fill="none", stroke="#1976d2", stroke_width=2
            )
        )
        dwg.add(dwg.text("R", insert=(x - 4, y + 4), font_size="10px", fill="#1976d2"))

    # Lights over bays
    for i in range(num_bays):
        x = bay_start_x + i * (bay_w + 10) + bay_w / 2
        y = bay_y - 30
        dwg.add(
            dwg.circle(
                center=(x, y), r=8, fill="none", stroke="#ffb300", stroke_width=2
            )
        )
        dwg.add(dwg.text("L", insert=(x - 4, y + 4), font_size="10px", fill="#ffb300"))

    dwg.add(
        dwg.text("ELECTRICAL PLAN", insert=(MARGIN + 20, HEIGHT - 30), font_size="24px")
    )
    dwg.save()


# ---------- HVAC Plan ----------


def create_hvac_plan():
    dwg, cust, parts, bays = base_drawing("facility_hvac_plan.svg")
    cust_x, cust_y, cust_w, cust_h = cust
    parts_x, parts_y, parts_w, parts_h = parts
    bay_start_x, bay_y, bay_w, bay_h, num_bays = bays

    # Rooftop units above customer and parts zones
    for i, (x0, label) in enumerate(
        [(cust_x + cust_w / 2, "RTU-1"), (parts_x + parts_w / 2, "RTU-2")]
    ):
        x = x0
        y = MARGIN - 10
        dwg.add(
            dwg.rect(
                insert=(x - 40, y - 30),
                size=(80, 40),
                fill="#e0f2f1",
                stroke="black",
                stroke_width=1,
            )
        )
        dwg.add(dwg.text(label, insert=(x - 25, y - 5), font_size="12px"))
        # Supply/return arrows down
        dwg.add(
            dwg.line(
                start=(x, y + 10), end=(x, cust_y), stroke="#00796b", stroke_width=2
            )
        )

    # Diffusers in customer zone
    for i in range(3):
        for j in range(2):
            x = cust_x + 80 + i * 150
            y = cust_y + 60 + j * 100
            dwg.add(
                dwg.rect(
                    insert=(x - 10, y - 10),
                    size=(20, 20),
                    fill="none",
                    stroke="#00796b",
                    stroke_width=2,
                )
            )
            dwg.add(
                dwg.text("D", insert=(x - 5, y + 5), font_size="10px", fill="#00796b")
            )

    # Supply air along bays
    duct_y = bay_y - 60
    dwg.add(
        dwg.line(
            start=(bay_start_x, duct_y),
            end=(bay_start_x + num_bays * (bay_w + 10), duct_y),
            stroke="#4e342e",
            stroke_width=4,
        )
    )
    for i in range(num_bays):
        x = bay_start_x + i * (bay_w + 10) + bay_w / 2
        dwg.add(
            dwg.line(
                start=(x, duct_y), end=(x, bay_y), stroke="#4e342e", stroke_width=2
            )
        )

    dwg.add(dwg.text("HVAC PLAN", insert=(MARGIN + 20, HEIGHT - 30), font_size="24px"))
    dwg.save()


# ---------- Plumbing Plan ----------


def create_plumbing_plan():
    dwg, cust, parts, bays = base_drawing("facility_plumbing_plan.svg")
    cust_x, cust_y, cust_w, cust_h = cust
    parts_x, parts_y, parts_w, parts_h = parts
    bay_start_x, bay_y, bay_w, bay_h, num_bays = bays

    # Restroom fixtures (schematic) in customer zone (bottom-right corner)
    rr_x = cust_x + cust_w - 160
    rr_y = cust_y + cust_h - 120
    dwg.add(
        dwg.rect(
            insert=(rr_x, rr_y),
            size=(150, 110),
            fill="none",
            stroke="#8d6e63",
            stroke_width=2,
        )
    )
    dwg.add(dwg.text("RESTROOM", insert=(rr_x + 10, rr_y + 20), font_size="12px"))

    # Toilets and sinks
    for i in range(2):
        x = rr_x + 30 + i * 50
        y = rr_y + 50
        dwg.add(
            dwg.circle(
                center=(x, y), r=8, fill="none", stroke="#5d4037", stroke_width=2
            )
        )
        dwg.add(
            dwg.text("WC", insert=(x - 12, y + 22), font_size="10px", fill="#5d4037")
        )
    for i in range(2):
        x = rr_x + 30 + i * 50
        y = rr_y + 90
        dwg.add(
            dwg.rect(
                insert=(x - 10, y - 6),
                size=(20, 12),
                fill="none",
                stroke="#5d4037",
                stroke_width=2,
            )
        )
        dwg.add(
            dwg.text("LAV", insert=(x - 14, y + 18), font_size="10px", fill="#5d4037")
        )

    # Water heater in parts / fluids area
    wh_x = parts_x + 60
    wh_y = parts_y + parts_h - 80
    dwg.add(
        dwg.circle(
            center=(wh_x, wh_y), r=18, fill="none", stroke="#1565c0", stroke_width=2
        )
    )
    dwg.add(
        dwg.text("WH", insert=(wh_x - 10, wh_y + 5), font_size="10px", fill="#1565c0")
    )

    # Cold water main
    main_y = MARGIN + 10
    dwg.add(
        dwg.line(
            start=(MARGIN + 40, main_y),
            end=(WIDTH - MARGIN - 40, main_y),
            stroke="#1565c0",
            stroke_width=3,
        )
    )
    dwg.add(
        dwg.text(
            "COLD WATER MAIN",
            insert=(MARGIN + 50, main_y - 10),
            font_size="12px",
            fill="#1565c0",
        )
    )

    # Drops to restroom and WH
    dwg.add(
        dwg.line(
            start=(cust_x + cust_w - 80, main_y),
            end=(cust_x + cust_w - 80, rr_y),
            stroke="#1565c0",
            stroke_width=2,
        )
    )
    dwg.add(
        dwg.line(
            start=(wh_x, main_y),
            end=(wh_x, wh_y - 18),
            stroke="#1565c0",
            stroke_width=2,
        )
    )

    # Floor drains in bays
    for i in range(0, num_bays, 3):
        x = bay_start_x + i * (bay_w + 10) + bay_w / 2
        y = bay_y + bay_h - 20
        dwg.add(
            dwg.circle(
                center=(x, y), r=6, fill="none", stroke="#00897b", stroke_width=2
            )
        )
        dwg.add(
            dwg.text("FD", insert=(x - 10, y + 18), font_size="10px", fill="#00897b")
        )

    dwg.add(
        dwg.text("PLUMBING PLAN", insert=(MARGIN + 20, HEIGHT - 30), font_size="24px")
    )
    dwg.save()


# ---------- Run all ----------


def run_all():
    create_electrical_plan()
    create_hvac_plan()
    create_plumbing_plan()
    print("Generated electrical, HVAC, and plumbing plans.")


if __name__ == "__main__":
    run_all()
