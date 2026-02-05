#!/usr/bin/env python3
"""Load an assembly STEP and print component names and metadata."""

import os
import sys

try:
    import cadquery as cq
except Exception:
    print("cadquery not available; run inside the cadquery conda env")
    raise

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
STEP = os.path.join(
    ROOT, "Python_Workflow", "outputs", "models", "facility_assembly.step"
)


def main(path: str = STEP) -> int:
    if not os.path.exists(path):
        print("STEP not found:", path)
        return 2
    print("Loading:", path)
    assy = cq.importers.importStep(path)
    objs = getattr(assy, "objects", None)
    if objs is None:
        # try Assembly.importStep
        try:
            assy = cq.Assembly.importStep(path)
            objs = getattr(assy, "objects", None)
        except Exception as e:
            print("Failed to import STEP:", e)
            return 3

    # if there are no objects, exit early to avoid iterating over None
    if not objs:
        print("No objects found in assembly")
        return 0

    print(f"Found {len(objs)} objects in assembly")
    for i, obj in enumerate(objs):
        name = getattr(obj, "name", None)
        meta = getattr(obj, "metadata", None)
        print(i, name, meta)
    return 0


if __name__ == "__main__":
    path = STEP
    if len(sys.argv) > 1:
        path = sys.argv[1]
    sys.exit(main(path))
