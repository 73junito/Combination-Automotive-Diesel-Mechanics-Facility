import svgwrite

WIDTH, HEIGHT = 2200, 900
MARGIN = 60

dwg = svgwrite.Drawing("facility_exterior_elevation.svg", size=(WIDTH, HEIGHT))

# Background
dwg.add(dwg.rect(insert=(0, 0), size=(WIDTH, HEIGHT), fill="#e3f2fd"))

# Ground
GROUND_Y = HEIGHT - 120
dwg.add(dwg.rect(insert=(0, GROUND_Y), size=(WIDTH, 120), fill="#cfd8dc"))

# Building body
BUILD_X = MARGIN
BUILD_Y = GROUND_Y - 320
BUILD_W = WIDTH - 2 * MARGIN
BUILD_H = 320

dwg.add(
    dwg.rect(
        insert=(BUILD_X, BUILD_Y),
        size=(BUILD_W, BUILD_H),
        fill="#eceff1",
        stroke="#37474f",
        stroke_width=3,
    )
)

# Roof band
dwg.add(dwg.rect(insert=(BUILD_X, BUILD_Y - 40), size=(BUILD_W, 40), fill="#455a64"))

# Main sign
dwg.add(
    dwg.text(
        "COMBINATION AUTOMOTIVE DIESEL MECHANICS FACILITY",
        insert=(BUILD_X + 80, BUILD_Y - 10),
        font_size="28px",
        fill="#ffffff",
    )
)

# Customer entrance block (left)
ENT_W, ENT_H = 260, 220
ENT_X = BUILD_X + 80
ENT_Y = BUILD_Y + BUILD_H - ENT_H

dwg.add(
    dwg.rect(
        insert=(ENT_X, ENT_Y),
        size=(ENT_W, ENT_H),
        fill="#fafafa",
        stroke="#455a64",
        stroke_width=2,
    )
)

# Glass doors
dwg.add(
    dwg.rect(
        insert=(ENT_X + 80, ENT_Y + 80),
        size=(40, 120),
        fill="#bbdefb",
        stroke="#1e88e5",
        stroke_width=2,
    )
)
dwg.add(
    dwg.rect(
        insert=(ENT_X + 120, ENT_Y + 80),
        size=(40, 120),
        fill="#bbdefb",
        stroke="#1e88e5",
        stroke_width=2,
    )
)

dwg.add(
    dwg.text(
        "CUSTOMER ENTRANCE",
        insert=(ENT_X + 20, ENT_Y + 60),
        font_size="18px",
        fill="#37474f",
    )
)

# Customer windows
for i in range(3):
    wx = ENT_X + 20 + i * 70
    wy = ENT_Y + 20
    dwg.add(
        dwg.rect(
            insert=(wx, wy),
            size=(50, 30),
            fill="#bbdefb",
            stroke="#1e88e5",
            stroke_width=2,
        )
    )

# Service bays (right side)
NUM_BAYS = 8
BAY_W = 120
BAY_H = 200
bay_start_x = BUILD_X + 450
bay_y = BUILD_Y + BUILD_H - BAY_H

for i in range(NUM_BAYS):
    x = bay_start_x + i * (BAY_W + 10)
    # Overhead door
    dwg.add(
        dwg.rect(
            insert=(x, bay_y),
            size=(BAY_W, BAY_H),
            fill="#eceff1",
            stroke="#607d8b",
            stroke_width=2,
        )
    )
    # Door panels
    for p in range(4):
        py = bay_y + 20 + p * 40
        dwg.add(
            dwg.line(
                start=(x + 5, py),
                end=(x + BAY_W - 5, py),
                stroke="#b0bec5",
                stroke_width=2,
            )
        )
    # Label
    dwg.add(
        dwg.text(
            f"BAY {i+1}", insert=(x + 25, bay_y - 10), font_size="14px", fill="#37474f"
        )
    )

# Service office sign above first bays
dwg.add(
    dwg.text(
        "SERVICE DEPARTMENT",
        insert=(bay_start_x, BUILD_Y + 40),
        font_size="22px",
        fill="#263238",
    )
)

# Parking in front of customer entrance
PARK_Y = GROUND_Y + 10
for i in range(6):
    px = BUILD_X + 40 + i * 120
    dwg.add(
        dwg.rect(
            insert=(px, PARK_Y),
            size=(90, 50),
            fill="#b0bec5",
            stroke="#455a64",
            stroke_width=2,
        )
    )

dwg.add(
    dwg.text(
        "CUSTOMER PARKING",
        insert=(BUILD_X + 40, PARK_Y - 10),
        font_size="16px",
        fill="#37474f",
    )
)

# Drive lane in front of bays
dwg.add(
    dwg.rect(
        insert=(bay_start_x - 40, GROUND_Y + 10),
        size=(NUM_BAYS * (BAY_W + 10) + 80, 60),
        fill="#b0bec5",
        stroke="none",
    )
)

dwg.add(
    dwg.text(
        "SERVICE DRIVE",
        insert=(bay_start_x, GROUND_Y + 50),
        font_size="16px",
        fill="#263238",
    )
)

# Simple trees / landscaping
for i in range(4):
    tx = WIDTH - MARGIN - 80
    ty = BUILD_Y + 40 + i * 80
    # trunk
    dwg.add(dwg.rect(insert=(tx + 18, ty + 30), size=(14, 40), fill="#6d4c41"))
    # canopy
    dwg.add(
        dwg.circle(
            center=(tx + 25, ty + 20),
            r=30,
            fill="#81c784",
            stroke="#388e3c",
            stroke_width=2,
        )
    )

dwg.add(
    dwg.text(
        "STREET FRONTAGE",
        insert=(MARGIN + 20, HEIGHT - 20),
        font_size="18px",
        fill="#37474f",
    )
)

dwg.save()
print("Generated facility_exterior_elevation.svg")
