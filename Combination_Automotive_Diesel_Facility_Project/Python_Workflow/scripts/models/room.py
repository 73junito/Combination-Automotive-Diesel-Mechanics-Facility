import cadquery as cq


def make_room(length=6000.0, width=4000.0, height=3000.0, wall_thickness=200.0):
    """Create a simple room volume as a box representing usable space.

    Units: millimeters. Returns a CadQuery solid placed with its floor at Z=0.
    """
    # Room is centered at origin in X/Y; floor rests at Z=0
    room = cq.Workplane("XY").box(length, width, height).translate((0, 0, height / 2.0))
    return room


if __name__ == "__main__":
    obj = make_room()
    cq.exporters.export(obj, "room_example.step")
