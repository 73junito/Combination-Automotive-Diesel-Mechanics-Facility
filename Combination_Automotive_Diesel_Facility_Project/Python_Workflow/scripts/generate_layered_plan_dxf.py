import os
from math import ceil

import ezdxf

"""
Simple layered DXF plan generator for the training facility.

Produces a plan DXF with discipline layers (A-*, E-*, P-*, M-*, F-*, EQ-*, FURN-*)
based on recommended defaults: 24 students, 12 light-duty bays, 4 heavy-duty bays,
integrated EV stations and both dedicated + shop classrooms.

Run from repo root (or from Python_Workflow) with the virtualenv active.
Dependencies: ezdxf (already listed in requirements.txt)
"""


def mm(val):
    return float(val)


def rect_points(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]


def add_rectangle(msp, layer, x, y, w, h, color=7):
    pts = rect_points(x, y, w, h)
    msp.add_lwpolyline(pts, dxfattribs={"layer": layer, "color": color})


def add_text(msp, layer, text, x, y, height=0.3, color=7):
    txt = msp.add_text(text, dxfattribs={"layer": layer, "color": color})
    try:
        txt.dxf.insert = (x, y)
        txt.dxf.height = height
    except Exception:
        # older/newer ezdxf variants may differ; best-effort positioning
        pass


def create_layers(doc):
    layers = [
        ("A-WALL-EXT", 1),
        ("A-WALL-INT", 1),
        ("A-DOOR", 3),
        ("A-GRID", 8),
        ("E-LIGHT-FIX", 6),
        ("E-POWER-OUT", 4),
        ("P-WATER", 5),
        ("P-DRAIN", 2),
        ("M-AHU", 9),
        ("M-EXHAUST", 10),
        ("F-ALARM", 1),
        ("EQ-LIFT", 3),
        ("EQ-COMP", 2),
        ("EQ-ALIGN", 3),
        ("EQ-CHARGE", 4),
        ("EQ-TOOLBOX", 5),
        ("EQ-FLAM", 1),
        ("EQ-BATT", 2),
        ("EQ-WASH", 2),
        ("E-PANEL", 1),
        ("E-POWER-3PH", 4),
        ("E-EMERG", 1),
        ("E-DATA", 5),
        ("P-AIR", 6),
        ("P-OILSEP", 2),
        ("M-VENT", 9),
        ("FURN-TABLE", 7),
        ("FURN-CHAIR", 7),
        ("FURN-DESK", 7),
        ("FURN-LOCKER", 7),
        ("FURN-STOR", 7),
        ("FURN-BOARD", 7),
        ("ROOM-LABEL", 7),
    ]
    for name, color in layers:
        if name not in doc.layers:
            doc.layers.new(name, dxfattribs={"color": color})


def generate_plan(
    output_path,
    student_count=24,
    light_bays=12,
    heavy_bays=4,
    light_lift_type="2-post",
    heavy_lift_type="4-post",
    ev_chargers=2,
):
    # Simple layout geometry in meters — adjustable by lift type
    aisle = 3.0

    def bay_dims(lift_type, heavy=False):
        """Return (width, depth) for a bay depending on lift type."""
        if lift_type == "2-post":
            # typical 2-post teaching lift footprint
            return (3.6, 7.0)
        if lift_type == "4-post":
            # wider/deeper for 4-post or alignment-capable lifts
            return (4.8, 9.0) if not heavy else (5.2, 10.0)
        # fallback
        return (3.6, 7.0)

    light_bay_w, light_bay_d = bay_dims(light_lift_type, heavy=False)
    heavy_bay_w, heavy_bay_d = bay_dims(heavy_lift_type, heavy=True)

    # Arrange light bays in two rows (respecting chosen lift dimensions)
    bays_per_row = int(ceil(light_bays / 2))
    shop_width = bays_per_row * light_bay_w * 2 + aisle
    shop_depth = light_bay_d * 2 + 4.0  # extra service space for working behind lift

    # Extra space for heavy bays along one side
    heavy_zone_w = heavy_bays * heavy_bay_w

    total_width = shop_width + heavy_zone_w + 2.0
    total_depth = max(shop_depth, heavy_bay_d + 6.0) + 4.0

    doc = ezdxf.new(dxfversion="R2010")
    create_layers(doc)
    msp = doc.modelspace()

    # Outer building shell
    add_rectangle(msp, "A-WALL-EXT", 0, 0, total_width, total_depth)
    add_text(msp, "ROOM-LABEL", "Training Facility Plan", 0.3, total_depth - 0.5)

    # Architectural: draw inner face of exterior walls to show wall thickness
    wall_thickness = 0.25
    inner_x = 0 + wall_thickness
    inner_y = 0 + wall_thickness
    inner_w = total_width - 2 * wall_thickness
    inner_h = total_depth - 2 * wall_thickness
    # inner wall line (A-WALL-INT) as closed polyline
    inner_pts = rect_points(inner_x, inner_y, inner_w, inner_h)
    msp.add_lwpolyline(inner_pts, dxfattribs={"layer": "A-WALL-INT", "color": 1})

    # Main entry door (coordination-only) centered on front (south) elevation
    door_w = 1.2
    door_h = 0.05
    door_x = (total_width - door_w) / 2
    door_y = 0
    add_rectangle(msp, "A-DOOR", door_x, door_y, door_w, door_h)

    # Structural grid: columns A..J and rows 1..6 for coordination
    grid_cols = 10
    grid_rows = 6
    col_spacing = total_width / grid_cols
    row_spacing = total_depth / grid_rows
    for i in range(grid_cols + 1):
        x = i * col_spacing
        msp.add_lwpolyline(
            [(x, 0), (x, total_depth)], dxfattribs={"layer": "A-GRID", "color": 8}
        )
        # label at top
        try:
            label = chr(ord("A") + (i if i < 26 else 25))
        except Exception:
            label = str(i)
        add_text(msp, "A-GRID", label, x + 0.05, total_depth - 0.1, height=0.25)
    for j in range(grid_rows + 1):
        y = j * row_spacing
        msp.add_lwpolyline(
            [(0, y), (total_width, y)], dxfattribs={"layer": "A-GRID", "color": 8}
        )
        add_text(msp, "A-GRID", str(j + 1), 0.1, y + 0.05, height=0.25)

    # Draw light-duty bays (two rows) with spacing derived from lift type
    start_x = 1.0
    start_y = 1.0
    light_positions = []
    for row in range(2):
        for i in range(bays_per_row):
            bay_index = row * bays_per_row + i
            if bay_index >= light_bays:
                continue
            x = start_x + i * (light_bay_w + 0.5)
            y = start_y + row * (light_bay_d + 1.5)
            add_rectangle(msp, "EQ-LIFT", x, y, light_bay_w - 0.1, light_bay_d - 0.1)
            light_positions.append((x, y, light_bay_w, light_bay_d))
            add_text(
                msp,
                "ROOM-LABEL",
                f"L-Bay {bay_index + 1}",
                x + 0.1,
                y + light_bay_d / 2,
            )

    # Heavy-duty bays along the right side — use heavy lift dims and required offsets
    heavy_x = shop_width + 1.0
    heavy_positions = []
    for i in range(heavy_bays):
        x = heavy_x + i * (heavy_bay_w + 0.6)
        y = 1.0
        add_rectangle(msp, "EQ-LIFT", x, y, heavy_bay_w - 0.1, heavy_bay_d - 0.1)
        heavy_positions.append((x, y, heavy_bay_w, heavy_bay_d))
        add_text(msp, "ROOM-LABEL", f"H-Bay {i + 1}", x + 0.1, y + heavy_bay_d / 2)

    # Equipment & tool placement
    # - Add rolling toolboxes near each light bay
    for row in range(2):
        for i in range(bays_per_row):
            bay_index = row * bays_per_row + i
            if bay_index >= light_bays:
                continue
            bx = start_x + i * light_bay_w
            by = start_y + row * (light_bay_d + 1.0)
            # toolbox positioned at bay's front corner
            tb_x = bx + 0.1
            tb_y = by - 0.6
            add_rectangle(msp, "EQ-TOOLBOX", tb_x, tb_y, 0.9, 0.5)
            add_text(msp, "ROOM-LABEL", f"TB {bay_index + 1}", tb_x, tb_y - 0.2)

    # Place EV chargers per requested count; prefer perimeter bays and avoid exhaust zones
    ev_count = min(ev_chargers, light_bays)
    charger_positions = []
    for e in range(ev_count):
        bx = start_x + e * (light_bay_w + 0.5)
        by = start_y
        ch_x = bx + light_bay_w - 0.6
        ch_y = by + light_bay_d + 0.4
        add_rectangle(msp, "EQ-CHARGE", ch_x, ch_y, 0.6, 0.8)
        add_text(msp, "ROOM-LABEL", f"EV Charger {e + 1}", ch_x, ch_y + 0.9)
        charger_positions.append((ch_x, ch_y))

    # Alignment rack near heavy bay zone
    align_x = heavy_x + 0.2
    align_y = heavy_bay_d + 1.0
    add_rectangle(msp, "EQ-ALIGN", align_x, align_y, 3.5, 1.8)
    add_text(msp, "ROOM-LABEL", "Alignment Rack", align_x + 0.1, align_y + 1.9)

    # Compressor room footprint near heavy bays (small room)
    comp_x = heavy_x + heavy_zone_w - 1.6
    comp_y = total_depth - 3.0
    add_rectangle(msp, "EQ-COMP", comp_x, comp_y, 1.4, 1.8)
    add_text(msp, "ROOM-LABEL", "Compressor", comp_x + 0.05, comp_y + 1.0)

    # Wash/detail bay at lower-left
    wash_x = 0.5
    wash_y = total_depth - 6.0
    add_rectangle(msp, "EQ-WASH", wash_x, wash_y, 3.0, 4.0)
    add_text(msp, "ROOM-LABEL", "Wash Bay", wash_x + 0.1, wash_y + 4.1)

    # Flammable and battery storage (fixed safe location)
    fs_x = heavy_x + heavy_zone_w + 0.5
    fs_y = total_depth - 4.0
    add_rectangle(msp, "EQ-FLAM", fs_x, fs_y, 0.8, 0.8)
    add_text(msp, "ROOM-LABEL", "Flammable", fs_x + 0.05, fs_y + 0.9)
    add_rectangle(msp, "EQ-BATT", fs_x + 0.95, fs_y, 0.8, 0.8)
    add_text(msp, "ROOM-LABEL", "Battery Storage", fs_x + 0.95, fs_y + 0.9)
    # Dedicated classroom (formal) - seating for student_count
    class_w, class_h = 9.6, 6.0
    class_x = 1.0
    class_y = total_depth - class_h - 1.0
    add_rectangle(msp, "A-WALL-INT", class_x, class_y, class_w, class_h)
    add_text(
        msp, "ROOM-LABEL", "Classroom (Formal)", class_x + 0.2, class_y + class_h - 0.5
    )

    # Classroom layout: compute rows/cols for student_count (max 6 cols preferred)
    preferred_cols = 6
    cols = min(preferred_cols, student_count)
    rows = int(ceil(student_count / cols))
    desk_w = 0.9
    desk_h = 0.55
    spacing_x = (class_w - cols * desk_w) / (cols + 1)
    spacing_y = (class_h - rows * desk_h) / (rows + 1)
    student = 0
    for r in range(rows):
        for c in range(cols):
            if student >= student_count:
                break
            tx = class_x + spacing_x + c * (desk_w + spacing_x)
            ty = class_y + spacing_y + r * (desk_h + spacing_y)
            add_rectangle(msp, "FURN-DESK", tx, ty, desk_w, desk_h)
            add_rectangle(msp, "FURN-CHAIR", tx + desk_w + 0.05, ty + 0.05, 0.35, 0.35)
            student += 1

    # Instructor station and whiteboard
    board_w, board_h = class_w - 0.4, 0.2
    board_x = class_x + 0.2
    board_y = class_y + class_h - board_h - 0.2
    add_rectangle(msp, "FURN-BOARD", board_x, board_y, board_w, board_h)
    inst_w, inst_h = 1.4, 0.7
    inst_x = class_x + (class_w - inst_w) / 2
    inst_y = board_y - inst_h - 0.3
    add_rectangle(msp, "FURN-DESK", inst_x, inst_y, inst_w, inst_h)
    add_text(msp, "ROOM-LABEL", "Instructor", inst_x + 0.1, inst_y + inst_h / 2)

    # Lockers along left wall (24 lockers)
    locker_w, locker_h = 0.6, 0.4
    lockers_per_row = 12
    lockers_x = class_x
    lockers_y = class_y - locker_h - 0.2
    for i in range(24):
        lx = lockers_x + (i % lockers_per_row) * (locker_w + 0.05)
        ly = lockers_y - (i // lockers_per_row) * (locker_h + 0.05)
        add_rectangle(msp, "FURN-LOCKER", lx, ly, locker_w, locker_h)

    # Shop-integrated teaching area (high-top tables + stools)
    teach_w, teach_h = 6.0, 3.0
    teach_x = class_x + class_w + 1.0
    teach_y = total_depth - teach_h - 1.0
    add_rectangle(msp, "FURN-TABLE", teach_x, teach_y, teach_w, teach_h)
    add_text(
        msp, "ROOM-LABEL", "Shop Teaching Zone", teach_x + 0.2, teach_y + teach_h - 0.3
    )
    # two high-top tables with stools
    ht_w, ht_h = 2.2, 0.7
    for i in range(2):
        htx = teach_x + 0.3 + i * (ht_w + 0.4)
        hty = teach_y + 0.6
        add_rectangle(msp, "FURN-TABLE", htx, hty, ht_w, ht_h)
        # stools
        for s in range(3):
            sx = htx + 0.2 + s * 0.6
            sy = hty - 0.4
            add_rectangle(msp, "FURN-CHAIR", sx, sy, 0.35, 0.35)

    # Tool storage wall
    stor_x = teach_x + teach_w + 0.5
    stor_y = teach_y
    add_rectangle(msp, "FURN-STOR", stor_x, stor_y, 1.2, teach_h)
    add_text(msp, "ROOM-LABEL", "Tool Storage", stor_x + 0.05, stor_y + teach_h - 0.3)

    # Architectural: shop boundary and internal doors (coordination-only)
    try:
        shop_x = start_x - 0.5
        shop_y = start_y - 0.5
        shop_w = shop_width
        shop_h = shop_depth
        shop_pts = rect_points(shop_x, shop_y, shop_w, shop_h)
        msp.add_lwpolyline(shop_pts, dxfattribs={"layer": "A-WALL-INT", "color": 1})

        # Door between classroom and shop (vertical door on classroom right face)
        cdoor_w = 0.05
        cdoor_h = 1.0
        cdoor_x = class_x + class_w
        cdoor_y = class_y + (class_h / 2) - (cdoor_h / 2)
        add_rectangle(msp, "A-DOOR", cdoor_x, cdoor_y, cdoor_w, cdoor_h)

        # Compressor personnel door (on compressor north face)
        pdoor_w = 0.05
        pdoor_h = 0.9
        pdoor_x = comp_x - pdoor_w
        pdoor_y = comp_y + 0.4
        add_rectangle(msp, "A-DOOR", pdoor_x, pdoor_y, pdoor_w, pdoor_h)
    except Exception:
        # ensure generator continues if any coords are missing
        pass

    # MEP placeholders aligned to equipment
    # Electrical: power drops at each lift and charger
    for idx, (lx, ly, lw, ld) in enumerate(light_positions):
        pd_x = lx + lw / 2
        pd_y = ly + ld + 0.2
        add_rectangle(msp, "E-POWER-OUT", pd_x - 0.15, pd_y - 0.15, 0.3, 0.3)
        add_text(msp, "ROOM-LABEL", f"Pwr L{idx + 1}", pd_x - 0.2, pd_y + 0.25)
        # compressed air drops
        air_x = lx + 0.2
        air_y = ly + ld - 0.5
        add_rectangle(msp, "P-AIR", air_x, air_y, 0.25, 0.25)
        add_text(msp, "ROOM-LABEL", f"Air L{idx + 1}", air_x, air_y - 0.3)
        # exhaust capture placeholder (light-duty symbol)
        ex_x = lx + lw / 2
        ex_y = ly + ld + 0.6
        add_rectangle(msp, "M-EXHAUST", ex_x - 0.25, ex_y - 0.1, 0.5, 0.2)
        add_text(msp, "ROOM-LABEL", f"Exhaust L{idx + 1}", ex_x - 0.4, ex_y + 0.25)

    for idx, (hx, hy, hw, hd) in enumerate(heavy_positions):
        pd_x = hx + hw - 0.5
        pd_y = hy + hd + 0.3
        # heavy lifts may require 3-phase
        add_rectangle(msp, "E-POWER-3PH", pd_x - 0.2, pd_y - 0.2, 0.4, 0.4)
        add_text(msp, "ROOM-LABEL", f"Pwr H{idx + 1} (3ph)", pd_x - 0.6, pd_y + 0.35)
        # compressed air
        air_x = hx + 0.3
        air_y = hy + hd - 0.6
        add_rectangle(msp, "P-AIR", air_x, air_y, 0.3, 0.3)
        add_text(msp, "ROOM-LABEL", f"Air H{idx + 1}", air_x, air_y - 0.3)
        # heavy exhaust symbol (larger)
        ex_x = hx + hw / 2
        ex_y = hy + hd + 0.9
        add_rectangle(msp, "M-EXHAUST", ex_x - 0.4, ex_y - 0.15, 0.8, 0.3)
        add_text(msp, "ROOM-LABEL", f"Exhaust H{idx + 1}", ex_x - 0.6, ex_y + 0.35)

    # Power and data at instructor station
    try:
        add_rectangle(msp, "E-POWER-OUT", inst_x + 0.1, inst_y + 0.1, 0.3, 0.3)
        add_rectangle(msp, "E-DATA", inst_x + inst_w - 0.4, inst_y + 0.1, 0.25, 0.25)
        add_text(msp, "ROOM-LABEL", "Data/Power Instructor", inst_x - 0.2, inst_y - 0.3)
    except NameError:
        pass

    # EV charger power points
    for idx, (cx, cy) in enumerate(charger_positions):
        add_rectangle(msp, "E-POWER-3PH", cx + 0.1, cy + 0.1, 0.4, 0.4)
        add_text(msp, "ROOM-LABEL", f"EV Pwr {idx + 1}", cx - 0.1, cy + 1.0)

    # Floor drains: heavy bays and wash bay
    for idx, (hx, hy, hw, hd) in enumerate(heavy_positions):
        d_x = hx + hw / 2
        d_y = hy + 0.3
        add_rectangle(msp, "P-DRAIN", d_x - 0.15, d_y - 0.15, 0.3, 0.3)
        add_text(msp, "ROOM-LABEL", f"Drain H{idx + 1}", d_x - 0.2, d_y + 0.4)

    # Wash bay drain
    add_rectangle(msp, "P-DRAIN", wash_x + 1.5, wash_y + 0.6, 0.4, 0.4)
    add_text(msp, "ROOM-LABEL", "Wash Drain", wash_x + 1.2, wash_y + 1.2)

    # Oil-water separator location (coordination only)
    ows_x = fs_x + 2.0
    ows_y = fs_y + 0.2
    add_rectangle(msp, "P-OILSEP", ows_x, ows_y, 0.6, 0.6)
    add_text(msp, "ROOM-LABEL", "Oil-Water Separator (coord)", ows_x - 0.2, ows_y + 0.9)

    # Panel placeholder near compressor
    add_rectangle(msp, "E-PANEL", comp_x + 0.2, comp_y + 0.2, 0.8, 1.2)
    add_text(msp, "ROOM-LABEL", "Elec Panel", comp_x + 0.2, comp_y + 1.5)

    # Emergency shutoffs: instructor + wash bay
    try:
        add_rectangle(msp, "E-EMERG", inst_x - 0.6, inst_y + inst_h / 2, 0.3, 0.3)
        add_text(msp, "ROOM-LABEL", "EMO", inst_x - 0.9, inst_y + inst_h / 2 + 0.4)
    except NameError:
        pass
    add_rectangle(msp, "E-EMERG", wash_x + 0.2, wash_y + 0.2, 0.3, 0.3)
    add_text(msp, "ROOM-LABEL", "EMO Wash", wash_x - 0.1, wash_y + 0.7)

    # Save file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.saveas(output_path)
    print(f"Generated layered DXF: {output_path}")


def export_disciplines(master_doc, out_folder):
    """Export separate DXF files by discipline using layer name prefixes."""
    os.makedirs(out_folder, exist_ok=True)
    mapping = {
        "ARCH": ["A-"],
        "ELEC": [
            "E-",
            "E-POWER-3PH",
            "E-PANEL",
            "E-EMERG",
            "E-DATA",
            "E-LIGHT-FIX",
            "E-POWER-OUT",
        ],
        "PLUMB": ["P-"],
        "MECH": ["M-"],
        "EQUIP": ["EQ-"],
        "FURN": ["FURN-"],
    }

    for name, prefixes in mapping.items():
        new_doc = ezdxf.new(dxfversion="R2010")
        new_msp = new_doc.modelspace()
        # copy relevant entities (supporting LWPOLYLINE and TEXT types created by generator)
        for e in master_doc.modelspace():
            layer = e.dxf.layer
            if any(layer.startswith(p) for p in prefixes):
                t = e.dxftype()
                color = getattr(e.dxf, "color", 7)
                try:
                    if t == "LWPOLYLINE":
                        pts = [
                            (p[0], p[1]) if len(p) >= 2 else (p[0], 0)
                            for p in e.get_points()
                        ]
                        new_msp.add_lwpolyline(
                            pts, dxfattribs={"layer": layer, "color": color}
                        )
                    elif t == "TEXT":
                        text = getattr(e.dxf, "text", "")
                        insert = getattr(e.dxf, "insert", (0, 0))
                        height = getattr(e.dxf, "height", 0.3)
                        nt = new_msp.add_text(
                            text, dxfattribs={"layer": layer, "color": color}
                        )
                        try:
                            nt.dxf.insert = insert
                            nt.dxf.height = height
                        except Exception:
                            pass
                    else:
                        # fallback: ignore unsupported types for now
                        pass
                except Exception:
                    # ignore individual entity errors to ensure export proceeds
                    continue

        out_path = os.path.join(out_folder, f"{name}_Plan.dxf")
        new_doc.saveas(out_path)
        print(f"Exported {name} DXF: {out_path}")


if __name__ == "__main__":
    out = os.path.join(
        os.path.dirname(__file__), "..", "outputs", "training_facility_plan_layered.dxf"
    )
    out = os.path.abspath(out)
    # Support a fast smoke mode for CI/testing via environment variable
    smoke = os.environ.get("SMOKE", "0")
    if smoke in ("1", "true", "True"):
        # small, fast generation for CI
        generate_plan(out, student_count=4, light_bays=2, heavy_bays=1, ev_chargers=1)
    else:
        generate_plan(out)
    # export separate discipline DXFs
    try:
        master = ezdxf.readfile(out)
        export_dir = os.path.join(os.path.dirname(out), "DXF")
        export_disciplines(master, export_dir)
    except Exception:
        print("Warning: failed to export discipline DXFs")
