import cadquery as cq


def make_two_post_lift(
    span=3000.0, post_height=2000.0, post_width=150.0, base_plate_thickness=20.0
):
    """Create a simple two-post lift representation: two columns and a top crossbar.

    Units: millimeters.
    Returns a CadQuery solid representing the assembled lift.
    """
    hx = span / 2.0 - post_width / 2.0

    post1 = (
        cq.Workplane("XY")
        .box(post_width, post_width, post_height)
        .translate((hx, 0.0, post_height / 2.0))
    )
    post2 = (
        cq.Workplane("XY")
        .box(post_width, post_width, post_height)
        .translate((-hx, 0.0, post_height / 2.0))
    )

    crossbar = (
        cq.Workplane("XY")
        .box(span + post_width, post_width / 2.0, post_width / 2.0)
        .translate((0.0, 0.0, post_height - post_width / 4.0))
    )

    base1 = (
        cq.Workplane("XY")
        .box(post_width * 2.0, post_width * 2.0, base_plate_thickness)
        .translate((hx, 0.0, base_plate_thickness / 2.0))
    )
    base2 = (
        cq.Workplane("XY")
        .box(post_width * 2.0, post_width * 2.0, base_plate_thickness)
        .translate((-hx, 0.0, base_plate_thickness / 2.0))
    )

    parts = [post1, post2, crossbar, base1, base2]
    compound = parts[0]
    for p in parts[1:]:
        compound = compound.union(p)

    return compound


if __name__ == "__main__":
    obj = make_two_post_lift()
    cq.exporters.export(obj, "two_post_lift_example.step")
