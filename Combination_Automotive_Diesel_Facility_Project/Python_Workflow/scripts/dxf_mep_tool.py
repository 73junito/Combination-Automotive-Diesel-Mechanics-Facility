#!/usr/bin/env python3
"""
DXF MEP Tool: audit layers/entities + ensure standard layer set + optional label injection + discipline-only exports.

Examples:
  python scripts/dxf_mep_tool.py --in training_facility_plan_layered.dxf --audit
  python scripts/dxf_mep_tool.py --in master.dxf --out master_with_layers.dxf --ensure-layers
  python scripts/dxf_mep_tool.py --in master.dxf --ensure-layers --export-disciplines out_dir
  python scripts/dxf_mep_tool.py --in master.dxf --ensure-layers --add-exhaust-labels 10 --out master_with_labels.dxf
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import ezdxf

# -----------------------------
# Layer standards (edit freely)
# -----------------------------
STANDARD_LAYERS: Dict[str, Dict] = {
    # Architecture
    "A-WALL-EXT": {"color": 7, "linetype": "CONTINUOUS"},
    "A-WALL-INT": {"color": 8, "linetype": "CONTINUOUS"},
    "A-DOOR": {"color": 3, "linetype": "CONTINUOUS"},
    "A-GRID": {"color": 9, "linetype": "DASHED"},
    "ROOM-LABEL": {"color": 2, "linetype": "CONTINUOUS"},
    # Electrical
    "E-LIGHT-FIX": {"color": 1, "linetype": "CONTINUOUS"},
    "E-POWER-OUT": {"color": 4, "linetype": "CONTINUOUS"},
    "E-PANEL": {"color": 5, "linetype": "CONTINUOUS"},
    "E-POWER-3PH": {"color": 6, "linetype": "CONTINUOUS"},
    "E-EMERG": {"color": 30, "linetype": "CONTINUOUS"},
    "E-DATA": {"color": 140, "linetype": "CONTINUOUS"},
    # Mechanical / HVAC
    "M-AHU": {"color": 94, "linetype": "CONTINUOUS"},
    "M-VENT": {"color": 96, "linetype": "CONTINUOUS"},
    "M-EXHAUST": {"color": 10, "linetype": "CONTINUOUS"},
    # Plumbing / Utilities
    "P-WATER": {"color": 151, "linetype": "CONTINUOUS"},
    "P-DRAIN": {"color": 152, "linetype": "CONTINUOUS"},
    "P-AIR": {"color": 153, "linetype": "CONTINUOUS"},
    "P-OILSEP": {"color": 154, "linetype": "CONTINUOUS"},
    # Fire / Safety placeholders
    "F-SUPPRESSION": {"color": 12, "linetype": "CONTINUOUS"},
    "F-EQUIP": {"color": 14, "linetype": "CONTINUOUS"},
}


DISCIPLINE_PATTERNS: Dict[str, List[str]] = {
    "ARCH": ["A-"],
    "ELEC": ["E-"],
    "MECH": ["M-"],
    "PLUMB": ["P-"],
    "FIRE": ["F-"],
    "EQUIP": ["EQ-", "EQUIP", "ASSET"],
}


def ensure_layer(
    doc: ezdxf.EzdxfDocument, name: str, color: int = 7, linetype: str = "CONTINUOUS"
) -> None:
    if name not in doc.layers:
        doc.layers.new(name=name, dxfattribs={"color": color, "linetype": linetype})
    else:
        layer = doc.layers.get(name)
        try:
            layer.dxf.color = color
            layer.dxf.linetype = linetype
        except Exception:
            pass


def ensure_standard_layers(doc: ezdxf.EzdxfDocument) -> None:
    try:
        # attempt to add a DASHED linetype; ignore if exists
        doc.linetypes.add("DASHED", pattern=[0.6, 0.3, -0.3])
    except Exception:
        pass

    for lname, spec in STANDARD_LAYERS.items():
        ensure_layer(
            doc,
            lname,
            color=spec.get("color", 7),
            linetype=spec.get("linetype", "CONTINUOUS"),
        )


def audit(doc: ezdxf.EzdxfDocument) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Return (entities_by_type, entities_by_layer)."""
    msp = doc.modelspace()
    by_type: Dict[str, int] = {}
    by_layer: Dict[str, int] = {}

    for e in msp:
        et = e.dxftype()
        by_type[et] = by_type.get(et, 0) + 1
        layer = getattr(e.dxf, "layer", "UNKNOWN")
        by_layer[layer] = by_layer.get(layer, 0) + 1

    return by_type, by_layer


def add_text(
    msp, text: str, x: float, y: float, layer: str, height: float = 0.25
) -> None:
    # prefer using set_placement when available
    try:
        tx = msp.add_text(text, dxfattribs={"layer": layer, "height": height})
        tx.set_placement((x, y))
    except Exception:
        msp.add_text(text, dxfattribs={"layer": layer, "height": height})


def add_exhaust_labels(
    doc: ezdxf.EzdxfDocument, n: int, start_xy=(0.0, 0.0), step=(5.0, 0.0)
) -> None:
    """Simple placeholder: places Exhaust L1..Ln as text in M-EXHAUST layer."""
    msp = doc.modelspace()
    x0, y0 = start_xy
    dx, dy = step
    ensure_layer(doc, "M-EXHAUST", color=10)
    for i in range(1, n + 1):
        add_text(
            msp,
            f"Exhaust L{i}",
            x0 + dx * (i - 1),
            y0 + dy * (i - 1),
            layer="M-EXHAUST",
            height=0.20,
        )


def write_audit_report(
    out_txt: Path, by_type: Dict[str, int], by_layer: Dict[str, int]
) -> None:
    lines: List[str] = []
    lines.append("DXF Audit Report")
    lines.append("=" * 40)
    lines.append("\nEntities by type:")
    for k in sorted(by_type.keys()):
        lines.append(f"  {k}: {by_type[k]}")
    lines.append("\nEntities by layer:")
    for k in sorted(by_layer.keys()):
        lines.append(f"  {k}: {by_layer[k]}")
    out_txt.write_text("\n".join(lines), encoding="utf-8")


def _layer_matches(layer: str, patterns: List[str]) -> bool:
    L = layer.upper()
    for p in patterns:
        if p.endswith("-"):
            if L.startswith(p.upper()):
                return True
        else:
            if p.upper() in L:
                return True
    return False


def export_disciplines(
    doc: ezdxf.EzdxfDocument, out_dir: Path, include_room_labels: bool = True
) -> List[Path]:
    """Create discipline-only DXF files in out_dir.

    The function attempts to copy entities that live on layers matching discipline prefixes.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []

    for disp, patterns in DISCIPLINE_PATTERNS.items():
        out_path = out_dir / f"{disp.lower()}_only.dxf"
        new_doc = ezdxf.new(
            dxfversion=doc.dxfversion if hasattr(doc, "dxfversion") else "R2010"
        )

        # copy over layer definitions for any layers that match
        layers_to_copy = set()
        # ezdxf LayerTable yields layer proxies; extract the layer names
        for lname in (l.dxf.name for l in doc.layers):
            if _layer_matches(lname, patterns):
                layers_to_copy.add(lname)
        if include_room_labels:
            layers_to_copy.add("ROOM-LABEL")

        # For MECH discipline, also include common mechanical layer name variants
        if disp == "MECH":
            mech_tokens = ("VENT", "DUCT", "AHU", "RTU", "MAKEUP", "RETURN")
            for lname in (l.dxf.name for l in doc.layers):
                LU = lname.upper()
                for tok in mech_tokens:
                    if tok in LU and LU not in layers_to_copy:
                        layers_to_copy.add(lname)
                        break

        # ensure layers exist in new doc
        for lname in sorted(layers_to_copy):
            try:
                src = doc.layers.get(lname)
                color = getattr(src.dxf, "color", 7)
            except Exception:
                color = 7
            ensure_layer(new_doc, lname, color=color)

        new_msp = new_doc.modelspace()

        # copy entities by layer
        def _explode_and_copy(insert_entity):
            """Explode a block INSERT and copy simple geometry into the target modelspace.

            This is a best-effort exploder: it applies a translation by the insert point
            (rotation/scale are not applied here to keep the code simple and robust).
            """
            try:
                block_name = insert_entity.dxf.name
            except Exception:
                return
            try:
                block = doc.blocks.get(block_name)
            except Exception:
                return
            ins_x, ins_y = 0.0, 0.0
            try:
                ins = insert_entity.dxf.insert
                ins_x, ins_y = float(ins[0]), float(ins[1])
            except Exception:
                pass

            for be in block:
                try:
                    blayer = getattr(be.dxf, "layer", "")
                    if blayer not in layers_to_copy:
                        # skip entities that aren't on a copied layer
                        continue
                    et = be.dxftype()
                    if et == "LINE":
                        s = be.dxf.start
                        e = be.dxf.end
                        new_msp.add_line(
                            (s[0] + ins_x, s[1] + ins_y),
                            (e[0] + ins_x, e[1] + ins_y),
                            dxfattribs={"layer": blayer},
                        )
                    elif et == "LWPOLYLINE":
                        try:
                            pts = [p[:2] for p in be.get_points()]
                        except Exception:
                            # fallback for legacy API
                            pts = [
                                (float(v[0]), float(v[1]))
                                for v in getattr(be, "points", [])
                            ]
                        if pts:
                            pts_t = [(x + ins_x, y + ins_y) for x, y in pts]
                            new_msp.add_lwpolyline(pts_t, dxfattribs={"layer": blayer})
                    elif et in ("TEXT", "MTEXT"):
                        try:
                            txt = (
                                be.get_text()
                                if hasattr(be, "get_text")
                                else getattr(be.dxf, "text", "")
                            )
                        except Exception:
                            txt = getattr(be.dxf, "text", "")
                        pos = getattr(be.dxf, "insert", (0.0, 0.0))
                        x, y = float(pos[0]) + ins_x, float(pos[1]) + ins_y
                        add_text(new_msp, txt, x, y, layer=blayer)
                    elif et == "CIRCLE":
                        c = be.dxf.center
                        new_msp.add_circle(
                            (c[0] + ins_x, c[1] + ins_y),
                            float(be.dxf.radius),
                            dxfattribs={"layer": blayer},
                        )
                    else:
                        # best-effort: try to copy the entity without transform
                        try:
                            ecopy = be.copy()
                            new_msp.add_entity(ecopy)
                        except Exception:
                            pass
                except Exception:
                    continue

        for e in doc.modelspace():
            layer = getattr(e.dxf, "layer", "")
            # If the entity is an INSERT, try to explode it and copy its contents
            if e.dxftype() == "INSERT":
                _explode_and_copy(e)
                # also keep the INSERT itself if it lives on a copied layer
                if layer in layers_to_copy:
                    try:
                        ecopy = e.copy()
                        new_msp.add_entity(ecopy)
                    except Exception:
                        pass
                continue
            if layer in layers_to_copy:
                try:
                    ecopy = e.copy()
                    new_msp.add_entity(ecopy)
                except Exception:
                    # best-effort fallback: try to recreate minimal text/lines
                    try:
                        etype = e.dxftype()
                        if etype == "TEXT" or etype == "MTEXT":
                            text = e.get_text() if hasattr(e, "get_text") else str(e)
                            pos = e.dxf.insert if hasattr(e.dxf, "insert") else (0, 0)
                            x, y = pos[0], pos[1]
                            add_text(new_msp, text, x, y, layer=layer)
                        elif etype == "LINE":
                            new_msp.add_line(
                                e.dxf.start, e.dxf.end, dxfattribs={"layer": layer}
                            )
                    except Exception:
                        pass

        new_doc.saveas(str(out_path))
        created.append(out_path)

    return created


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True, help="Input DXF path")
    p.add_argument("--out", dest="out", default="", help="Output DXF path (optional)")
    p.add_argument(
        "--audit",
        action="store_true",
        help="Write audit report next to output (or input)",
    )
    p.add_argument(
        "--ensure-layers", action="store_true", help="Ensure standard layer set exists"
    )
    p.add_argument(
        "--add-exhaust-labels",
        type=int,
        default=0,
        help="Add Exhaust L1..Ln labels (placeholder)",
    )
    p.add_argument("--exhaust-start-x", type=float, default=10.0)
    p.add_argument("--exhaust-start-y", type=float, default=10.0)
    p.add_argument("--exhaust-step-x", type=float, default=5.0)
    p.add_argument("--exhaust-step-y", type=float, default=0.0)
    p.add_argument(
        "--export-disciplines",
        dest="export_disciplines",
        default="",
        help="Directory to write discipline-only DXFs",
    )
    args = p.parse_args()

    inp = Path(args.inp).resolve()
    if not inp.exists():
        raise SystemExit(f"Input DXF not found: {inp}")

    doc = ezdxf.readfile(str(inp))

    if args.ensure_layers:
        ensure_standard_layers(doc)

    if args.add_exhaust_labels > 0:
        add_exhaust_labels(
            doc,
            n=args.add_exhaust_labels,
            start_xy=(args.exhaust_start_x, args.exhaust_start_y),
            step=(args.exhaust_step_x, args.exhaust_step_y),
        )

    # Determine output target
    if args.out:
        out_dxf = Path(args.out).resolve()
    else:
        out_dxf = inp.with_name(inp.stem + "_mep.dxf")

    doc.saveas(str(out_dxf))
    print("WROTE DXF:", out_dxf)

    if args.audit:
        by_type, by_layer = audit(doc)
        out_txt = out_dxf.with_suffix(".audit.txt")
        write_audit_report(out_txt, by_type, by_layer)
        print("WROTE AUDIT:", out_txt)

    if args.export_disciplines:
        out_dir = Path(args.export_disciplines)
        created = export_disciplines(doc, out_dir, include_room_labels=True)
        for pth in created:
            print("WROTE DISCIPLINE DXF:", pth)


if __name__ == "__main__":
    main()
