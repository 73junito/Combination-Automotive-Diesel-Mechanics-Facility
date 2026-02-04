import cadquery as cq


def make_duct(length=2000.0, width=400.0, height=200.0):
    """Create a simple rectangular duct volume.

    Units: millimeters. Returns a CadQuery solid aligned with XY plane.
    """
    duct = (
        cq.Workplane("XY")
        .box(length, width, height)
        .translate((length / 2.0, 0.0, height / 2.0))
    )
    return duct


if __name__ == "__main__":
    obj = make_duct()
    cq.exporters.export(obj, "duct_example.step")
