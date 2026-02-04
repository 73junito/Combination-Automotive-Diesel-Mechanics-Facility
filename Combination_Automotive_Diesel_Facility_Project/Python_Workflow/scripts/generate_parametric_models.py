"""Runner to generate parametric equipment models and export STEP/STL files.

Usage:
  python generate_parametric_models.py [--export-stl]

By default the script exports STEP files to `outputs/models/`.
If `--export-stl` is provided, STL files are also written to `outputs/models/stl/`.

Run in a Python environment with CadQuery available.
"""

import argparse
import sys
from pathlib import Path

try:
    import cadquery as cq
except Exception as e:
    print("CadQuery import failed:", e)
    print(
        "Install CadQuery (e.g. pip install cadquery) or add local source to PYTHONPATH."
    )
    sys.exit(1)

from models.bay import make_bay
from models.lift import make_two_post_lift
from models.workbench import make_workbench


def export_model(obj, out_dir: Path, name: str, fmt: str = "STEP"):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir.joinpath(f"{name}.{fmt.lower()}")
    try:
        cq.exporters.export(obj, str(path))
        print(f"Exported {name} -> {path}")
        return str(path)
    except Exception as e:
        print(f"Failed exporting {name} ({fmt}): {e}")
        return None


def make_models(export_stl: bool = False):
    root = Path(__file__).parent.parent
    out_step = root.joinpath("outputs", "models")
    out_stl = root.joinpath("outputs", "models", "stl") if export_stl else None

    models = [
        (make_bay(), "bay"),
        (make_workbench(), "workbench"),
        (make_two_post_lift(), "two_post_lift"),
    ]

    results = {"step": [], "stl": []}

    for obj, name in models:
        s = export_model(obj, out_step, name, "STEP")
        if s:
            results["step"].append(s)
        if export_stl and out_stl is not None:
            stl_path = export_model(obj, out_stl, name, "STL")
            if stl_path:
                results["stl"].append(stl_path)

    return results


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate parametric models and export STEP/STL files."
    )
    p.add_argument(
        "--export-stl",
        action="store_true",
        help="Also export binary STL files to outputs/models/stl/",
    )
    return p.parse_args()


def main():
    args = parse_args()
    results = make_models(export_stl=args.export_stl)
    print("Summary:")
    print(" STEP files:")
    for f in results.get("step", []):
        print("  -", f)
    if args.export_stl:
        print(" STL files:")
        for f in results.get("stl", []):
            print("  -", f)


if __name__ == "__main__":
    main()
