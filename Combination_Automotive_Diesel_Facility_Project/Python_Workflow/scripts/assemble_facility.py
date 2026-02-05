#!/usr/bin/env python3
"""Assemble facility from DXF block inserts and export STEP/STL.

Searches for INSERT entities on the `EQUIP_LABELS` layer in
`outputs/facility_layout_blocks.dxf` and places parametric models
(e.g. `bay`, `workbench`, `two_post_lift`, `room`, `duct`) at those insert points.

The script exports:
- a componentized STEP (`facility_assembly_components.step`) with per-component product
    names/metadata when OCP/STEPCAF is available (recommended for BIM/product searchability),
- per-part STEP files to `outputs/models/components/` as a fallback, and
- a unioned STEP (`facility_assembly.step`) and unioned STL (`stl/facility_assembly.stl`) when
    `--union` is specified (useful for quick visualization and bounding-box checks).

The STEP CAF export requires optional runtime packages `ocp` and `pythonocc-core`. If those
are not installed the script will still produce unioned and per-part STEP/STL outputs.
"""

import argparse
import csv
import math
import os
import runpy
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, Optional

# module-level placeholders so mypy understands conditional imports
ezdxf: Optional[ModuleType] = None
cq: Optional[ModuleType] = None
# OCP / pythonocc types are classes from binary packages; use object for narrowness
STEPCAFControl_Writer: Optional[object] = None
TDocStd_Document: Optional[object] = None
XCAFApp_Application: Optional[object] = None
TCollection_AsciiString: Optional[object] = None
XCAFDoc_DocumentTool_ShapeTool: Optional[object] = None
TDataStd_Name: Optional[object] = None
TCollection_ExtendedString: Optional[object] = None

try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except Exception:
    ezdxf = None

try:
    import cadquery as _cq

    cq = _cq
except Exception:
    cq = None

try:
    # OCP / pythonocc - used for STEP CAF export (product contexts / names)
    from OCP.STEPCAFControl import \
        STEPCAFControl_Writer as _STEPCAFControl_Writer
    from OCP.TCollection import \
        TCollection_AsciiString as _TCollection_AsciiString
    from OCP.TCollection import \
        TCollection_ExtendedString as _TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name as _TDataStd_Name
    from OCP.TDocStd import TDocStd_Document as _TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application as _XCAFApp_Application
    from OCP.XCAFDoc import \
        XCAFDoc_DocumentTool_ShapeTool as _XCAFDoc_DocumentTool_ShapeTool

    STEPCAFControl_Writer = _STEPCAFControl_Writer
    TDocStd_Document = _TDocStd_Document
    XCAFApp_Application = _XCAFApp_Application
    TCollection_AsciiString = _TCollection_AsciiString
    XCAFDoc_DocumentTool_ShapeTool = _XCAFDoc_DocumentTool_ShapeTool
    TDataStd_Name = _TDataStd_Name
    TCollection_ExtendedString = _TCollection_ExtendedString
except Exception:
    STEPCAFControl_Writer = None
    TDocStd_Document = None
    XCAFApp_Application = None
    TCollection_AsciiString = None
    XCAFDoc_DocumentTool_ShapeTool = None
    TDataStd_Name = None
    TCollection_ExtendedString = None


ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Python_Workflow", "outputs")
DXF_DEFAULT = os.path.join(OUT, "facility_layout_blocks.dxf")
MODELS_DIR = os.path.join(ROOT, "Python_Workflow", "scripts", "models")


def load_factory(pyfile, factory_name):
    path = os.path.join(MODELS_DIR, pyfile)
    if not os.path.exists(path):
        return None
    glb = runpy.run_path(path)
    return glb.get(factory_name)


# model key -> (python file, factory function name)
MODEL_FACTORY_MAP = {
    "bay": ("bay.py", "make_bay"),
    "workbench": ("workbench.py", "make_workbench"),
    "two_post_lift": ("lift.py", "make_two_post_lift"),
    "room": ("room.py", "make_room"),
    "duct": ("duct.py", "make_duct"),
}


def choose_factory_by_model_key(model_key):
    if not model_key:
        return None
    key = model_key.strip().lower()
    if key in MODEL_FACTORY_MAP:
        pyfile, fname = MODEL_FACTORY_MAP[key]
        return load_factory(pyfile, fname)
    return None


CONFIG_DIR = os.path.join(ROOT, "Python_Workflow", "config")
CONFIG_CSV = os.path.join(CONFIG_DIR, "equipment_map.csv")


def load_csv_map(path):
    """Return dict mapping block_name -> (model_key, z_offset, rotation_deg)."""
    if not os.path.exists(path):
        return {}
    m = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = (row.get("block_name") or "").strip()
            if not name:
                continue
            model = (row.get("model") or "").strip()
            try:
                z = float((row.get("z_offset_mm") or 0) or 0)
            except Exception:
                z = 0.0
            try:
                rot = float((row.get("rotation_deg") or 0) or 0)
            except Exception:
                rot = 0.0
            m[name] = (model, z, rot)
    return m


def main(
    dxf_path,
    export_stl=False,
    out_step=None,
    out_stl=None,
    systems_filter=None,
    do_union=False,
):
    if ezdxf is None:
        print(
            "ezdxf is not installed; install with 'pip install ezdxf' or use the cadquery env."
        )
        raise SystemExit(1)
    if cq is None:
        print("cadquery not available; run inside the cadquery conda environment.")
        raise SystemExit(2)

    if not os.path.exists(dxf_path):
        print("DXF not found:", dxf_path)
        raise SystemExit(3)

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    placements = []
    for e in msp:
        try:
            layer = e.dxf.layer
        except AttributeError:
            continue
        # look for equipment label inserts
        if layer != "EQUIP_LABELS":
            continue
        if e.dxftype() != "INSERT":
            continue
        block_name = e.dxf.name
        insert = tuple(getattr(e.dxf, "insert", (0.0, 0.0, 0.0)))
        rotation = getattr(e.dxf, "rotation", 0.0) or 0.0
        placements.append((block_name, insert, rotation))

    if not placements:
        print("No INSERTs found on layer EQUIP_LABELS in", dxf_path)
        return

    # load CSV map (block_name -> model_key,z_offset,rotation, optional fields)
    csv_map = load_csv_map(CONFIG_CSV)
    # allow overriding CSV path via env or CLI later (CLI added at bottom)

    # systems_filter and do_union are passed in from CLI

    parts = []
    mapped = 0
    skipped = 0
    for i, (blk, ins, rot) in enumerate(placements):
        # CSV mapping takes precedence
        entry = csv_map.get(blk)
        if entry:
            model_key, z_offset, csv_rot = entry
        else:
            model_key, z_offset, csv_rot = (None, 0.0, 0.0)

        factory = choose_factory_by_model_key(model_key)
        # systems filter: determine system category for model_key
        MODEL_SYSTEM_MAP = {
            "room": "rooms",
            "duct": "mechanical",
            "bay": "furniture",
            "workbench": "furniture",
            "two_post_lift": "furniture",
        }
        if systems_filter:
            system = MODEL_SYSTEM_MAP.get((model_key or "").lower())
            if system not in systems_filter:
                print(f"Skipping '{blk}' -> {model_key} due to system filter")
                skipped += 1
                continue
        if factory is None:
            print(f"Skipping unknown block '{blk}' at {ins}")
            skipped += 1
            continue
        mapped += 1
        print(
            f"Placing '{blk}' -> {model_key} at {ins} rot_csv={csv_rot} rot_dxf={rot} z_offset={z_offset}"
        )
        # create model (CadQuery Workplane/solid)
        obj = factory()
        # apply rotation: prefer CSV-specified rotation if non-zero, else DXF rotation
        use_rot = csv_rot if csv_rot else rot
        if use_rot:
            try:
                obj = obj.rotate((0, 0, 0), (0, 0, 1), float(use_rot))
            except Exception:
                pass
        # translate to XY insert and apply z offset
        x, y = float(ins[0]), float(ins[1])
        z = float(z_offset or 0.0)
        try:
            obj = obj.translate((x, y, z))
        except Exception:
            try:
                obj = obj.val().Translated(cq.Vector(x, y, z))
            except Exception:
                pass
        parts.append((blk, model_key, obj, use_rot, z))

    if not parts:
        print("No parts to assemble after mapping blocks.")
        print(f"Found {len(placements)} INSERTs; mapped {mapped}; skipped {skipped}")
        return

    out_models_dir = os.path.join(OUT, "models")
    os.makedirs(out_models_dir, exist_ok=True)
    if out_step is None:
        out_step = os.path.join(out_models_dir, "facility_assembly.step")
    # Always build an Assembly with separate components so we can export
    # a componentized STEP containing per-component names/metadata.
    assy = cq.Assembly(name="facility")
    for idx, (blk, model_key, obj, use_rot, z) in enumerate(parts):
        name = f"{model_key}_{idx}"
        metadata = {
            "name": f"{model_key}_{blk}",
            "equipment_type": model_key,
            "block_name": blk,
            "source_layer": "EQUIP_LABELS",
            "rotation_deg": float(use_rot or 0.0),
            "z_offset_mm": float(z or 0.0),
        }
        try:
            assy.add(obj, name=name, metadata=metadata)
        except Exception:
            # fallback: try to add raw shape
            try:
                assy.add(obj.val(), name=name, metadata=metadata)
            except Exception:
                print(f"Warning: failed to add part {name} to assembly")

    # Export componentized STEP with per-component names/metadata
    components_step = os.path.join(out_models_dir, "facility_assembly_components.step")
    print("Exporting componentized STEP ->", components_step)
    wrote_components = False
    # Try STEP CAF export first (preferred) so product names are preserved
    if STEPCAFControl_Writer is not None:
        try:

            def export_step_caf(parts_list, target_path):
                app = XCAFApp_Application.GetApplication()
                doc = TDocStd_Document(TCollection_AsciiString("python"))
                # Create a new XDE document (MDTV-Standard style)
                app.NewDocument(TCollection_AsciiString("MDTV-Standard"), doc)
                shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
                labels = []
                for idx, (blk, model_key, p, use_rot, z) in enumerate(parts_list):
                    try:
                        shp = p.val()
                    except Exception:
                        shp = p
                    lab = shape_tool.AddShape(shp)
                    # set the product/name
                    try:
                        TDataStd_Name.Set(
                            lab, TCollection_ExtendedString(f"{model_key}_{blk}")
                        )
                    except Exception:
                        pass
                    labels.append(lab)
                # initialize writer and transfer document
                writer = STEPCAFControl_Writer()
                try:
                    # Transfer XDE document to STEP writer
                    ok = writer.Transfer(doc, STEPCAFControl_Writer.Mode())
                except Exception:
                    try:
                        ok = writer.Transfer(doc)
                    except Exception:
                        ok = False
                if not ok:
                    raise RuntimeError("STEP CAF transfer failed")
                # write file
                res = writer.Write(target_path)
                if res != 1:
                    raise RuntimeError(f"STEP CAF write failed: {res}")

            export_step_caf(parts, components_step)
            wrote_components = True
        except Exception as exc:
            print("Warning: STEP CAF export failed:", exc)

    if not wrote_components:
        try:
            cq.exporters.export(assy, components_step)
            wrote_components = True
        except Exception:
            print("Warning: failed to export componentized STEP via assembly exporter")
            # Fallback: write each part as its own STEP file into a components folder
            comp_dir = os.path.join(out_models_dir, "components")
            os.makedirs(comp_dir, exist_ok=True)
            for idx, (blk, model_key, p, use_rot, z) in enumerate(parts):
                fname = f"{model_key}_{blk}.step"
                fpath = os.path.join(comp_dir, fname)
                try:
                    cq.exporters.export(p, fpath)
                except Exception:
                    try:
                        cq.exporters.export(p.val(), fpath)
                    except Exception:
                        print(f"Failed to export individual part STEP: {fname}")
            print(f"Wrote individual component STEP files to: {comp_dir}")

    # If --union requested, create a fused compound and export unioned STEP/STL
    compound = None
    if do_union:
        compound = parts[0][2]
        for _, _, p, _, _ in parts[1:]:
            try:
                compound = compound.union(p)
            except Exception:
                try:
                    compound = compound.union(p.val())
                except Exception:
                    pass

        print("Exporting unioned STEP ->", out_step)
        try:
            cq.exporters.export(compound, out_step)
        except Exception:
            print("Warning: failed to export unioned STEP via compound exporter")

        if export_stl:
            if out_stl is None:
                stl_dir = os.path.join(out_models_dir, "stl")
                os.makedirs(stl_dir, exist_ok=True)
                out_stl = os.path.join(stl_dir, "facility_assembly.stl")
            print("Exporting unioned STL ->", out_stl)
            try:
                cq.exporters.export(compound, out_stl)
            except Exception:
                print("Failed to export unioned STL")
    else:
        # If not unioning, export the assembly STEP as the main STEP
        print("Exporting STEP ->", out_step)
        try:
            cq.exporters.export(assy, out_step)
        except Exception:
            print("Warning: failed to export assembly STEP via exporters.export")
        if export_stl:
            if out_stl is None:
                stl_dir = os.path.join(out_models_dir, "stl")
                os.makedirs(stl_dir, exist_ok=True)
                out_stl = os.path.join(stl_dir, "facility_assembly.stl")
            print("Exporting STL ->", out_stl)
            try:
                cq.exporters.export(assy, out_stl)
            except Exception:
                print("Failed to export STL for assembly")

    print(f"Found {len(placements)} INSERTs; mapped {mapped}; skipped {skipped}")

    # compute bounding box from exported STL if available
    if export_stl and os.path.exists(out_stl):
        try:
            mins, maxs = parse_stl_bbox(out_stl)
            dims = tuple(maxs[i] - mins[i] for i in range(3))
            print(
                f"Facility bounding box (X×Y×Z): {dims[0]:.3f} × {dims[1]:.3f} × {dims[2]:.3f} (assumed mm)"
            )
            print(f" Min: ({mins[0]:.3f}, {mins[1]:.3f}, {mins[2]:.3f})")
            print(f" Max: ({maxs[0]:.3f}, {maxs[1]:.3f}, {maxs[2]:.3f})")
        except Exception:
            print("Could not compute bounding box from STL")


def parse_stl_bbox(path):
    import struct

    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 84:
        raise ValueError("STL too small")
    header_start = data[:5].decode("utf-8", errors="ignore").lower()
    as_text = False
    if header_start.startswith("solid") and b"facet" in data:
        try:
            text = data.decode("utf-8")
            as_text = True
        except Exception:
            as_text = False
    if as_text:
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                parts = line.split()
                if len(parts) >= 4:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    mins[0] = min(mins[0], x)
                    mins[1] = min(mins[1], y)
                    mins[2] = min(mins[2], z)
                    maxs[0] = max(maxs[0], x)
                    maxs[1] = max(maxs[1], y)
                    maxs[2] = max(maxs[2], z)
        return tuple(mins), tuple(maxs)
    else:
        try:
            tri_count = struct.unpack_from("<I", data, 80)[0]
        except Exception:
            # fallback to ascii parsing
            text = data.decode("utf-8", errors="ignore")
            mins = [float("inf")] * 3
            maxs = [float("-inf")] * 3
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("vertex"):
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        mins[0] = min(mins[0], x)
                        mins[1] = min(mins[1], y)
                        mins[2] = min(mins[2], z)
                        maxs[0] = max(maxs[0], x)
                        maxs[1] = max(maxs[1], y)
                        maxs[2] = max(maxs[2], z)
            return tuple(mins), tuple(maxs)
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        offset = 84
        for i in range(tri_count):
            if offset + 50 > len(data):
                break
            chunk = data[offset : offset + 50]
            vals = struct.unpack("<12f", chunk[:48])
            verts = [
                (vals[3], vals[4], vals[5]),
                (vals[6], vals[7], vals[8]),
                (vals[9], vals[10], vals[11]),
            ]
            for x, y, z in verts:
                mins[0] = min(mins[0], x)
                mins[1] = min(mins[1], y)
                mins[2] = min(mins[2], z)
                maxs[0] = max(maxs[0], x)
                maxs[1] = max(maxs[1], y)
                maxs[2] = max(maxs[2], z)
            offset += 50
        return tuple(mins), tuple(maxs)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Assemble facility from DXF block inserts")
    p.add_argument("--dxf", default=DXF_DEFAULT, help="DXF file with block inserts")
    p.add_argument(
        "--csv",
        default=CONFIG_CSV,
        help="CSV mapping file (block_name -> model,z_offset_mm,rotation_deg)",
    )
    p.add_argument(
        "--export-stl",
        action="store_true",
        help="Also export STL (componentized or unioned depending on flags)",
    )
    p.add_argument(
        "--systems",
        default=None,
        help="Comma-separated systems to include (rooms,mechanical,furniture)",
    )
    p.add_argument(
        "--union",
        action="store_true",
        help=(
            "Union all parts into a single solid before export."
            " When used the script will also export a unioned STEP/STL."
        ),
    )
    args = p.parse_args()
    # allow CSV override
    CONFIG_CSV = args.csv
    systems_filter = None
    if args.systems:
        systems_filter = set(
            s.strip().lower() for s in args.systems.split(",") if s.strip()
        )
    main(
        args.dxf,
        export_stl=args.export_stl,
        out_step=None,
        out_stl=None,
        systems_filter=systems_filter,
        do_union=bool(args.union),
    )
