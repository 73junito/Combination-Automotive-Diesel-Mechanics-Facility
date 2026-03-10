import cadquery as cq


def make_workbench(
    width=1200.0, depth=600.0, height=900.0, top_thickness=25.0, leg_diameter=40.0
):
    """Create a simple workbench: rectangular top and four cylindrical legs.

    Units: millimeters.
    Returns a CadQuery solid representing the assembled workbench.
    """
    # top
    top = (
        cq.Workplane("XY")
        .box(width, depth, top_thickness)
        .translate((0.0, 0.0, height - top_thickness / 2.0))
    )

    # legs - place near corners inset by 50 mm
    inset = 50.0
    hx = width / 2.0 - inset
    hy = depth / 2.0 - inset
    legs = []
    for sx in (hx, -hx):
        for sy in (hy, -hy):
            leg = (
                cq.Workplane("XY")
                .circle(leg_diameter / 2.0)
                .extrude(height - top_thickness)
                .translate((sx, sy, (height - top_thickness) / 2.0))
            )
            legs.append(leg)

    parts = [top] + legs
    compound = parts[0]
    for p in parts[1:]:
        compound = compound.union(p)

    return compound


if __name__ == "__main__":
    obj = make_workbench()
    cq.exporters.export(obj, "workbench_example.step")
