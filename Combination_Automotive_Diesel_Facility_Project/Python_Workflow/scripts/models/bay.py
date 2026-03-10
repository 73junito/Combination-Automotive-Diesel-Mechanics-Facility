import cadquery as cq


def make_bay(
    width=3000.0, depth=6000.0, height=2400.0, post_size=100.0, beam_height=150.0
):
    """Create a simple four-post bay with top beams.

    Units: millimeters.
    Returns a CadQuery solid representing the assembled bay.
    """
    # corner offsets
    hx = width / 2.0 - post_size / 2.0
    hy = depth / 2.0 - post_size / 2.0

    posts = []
    for sx in (hx, -hx):
        for sy in (hy, -hy):
            p = (
                cq.Workplane("XY")
                .box(post_size, post_size, height)
                .translate((sx, sy, height / 2.0))
            )
            posts.append(p)

    # top beams (front/back and left/right)
    beam_thickness = post_size / 2.0
    beam_x = (
        cq.Workplane("XY")
        .box(width, beam_thickness, beam_height)
        .translate((0.0, hy, height - beam_height / 2.0))
    )
    beam_x2 = (
        cq.Workplane("XY")
        .box(width, beam_thickness, beam_height)
        .translate((0.0, -hy, height - beam_height / 2.0))
    )
    beam_y = (
        cq.Workplane("XY")
        .box(beam_thickness, depth, beam_height)
        .translate((hx, 0.0, height - beam_height / 2.0))
    )
    beam_y2 = (
        cq.Workplane("XY")
        .box(beam_thickness, depth, beam_height)
        .translate((-hx, 0.0, height - beam_height / 2.0))
    )

    parts = posts + [beam_x, beam_x2, beam_y, beam_y2]

    # combine parts into a single solid
    compound = parts[0]
    for part in parts[1:]:
        compound = compound.union(part)

    return compound


if __name__ == "__main__":
    obj = make_bay()
    cq.exporters.export(obj, "bay_example.step")
