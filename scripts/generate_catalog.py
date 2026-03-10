#!/usr/bin/env python3
"""Generate a simple drawing catalog markdown file with previews.

Scans `Drawings/CAD/` for CAD files and links previews from `Drawings/Previews/`.

Usage:
  python scripts/generate_catalog.py

Options:
  --cad-dir DIR       (default: Drawings/CAD)
  --preview-dir DIR   (default: Drawings/Previews)
  --output FILE       (default: Drawings/catalog.md)
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

FILE_EXTS = {".dwg", ".dxf", ".cdl", ".cqx", ".pdf"}


def find_cad_files(cad_dir: Path) -> List[Path]:
    items: List[Path] = []
    if not cad_dir.exists():
        return items
    for ext in FILE_EXTS:
        items.extend(cad_dir.rglob(f"*{ext}"))
    # dedupe and sort deterministically
    unique = sorted(
        {p.resolve(): p for p in items}.values(), key=lambda p: p.name.lower()
    )
    return unique


def parse_name(stem: str) -> Tuple[str, str, str, str]:
    """Parse a file stem into (project, discipline, display_name, revision).

    This uses a flexible heuristic:
      - project: first dash-separated token
      - discipline: second token if present
      - revision: matches `_revNN` or `_revN` case-insensitive
      - display_name: the original stem
    """
    rev = ""
    m = re.search(r"[_-]rev(\d{1,3})$", stem, flags=re.IGNORECASE)
    if m:
        rev = f"rev{m.group(1).zfill(2)}"

    parts = stem.split("-")
    project = parts[0] if parts else "Unknown"
    discipline = parts[1] if len(parts) > 1 else "General"
    display = stem
    return project, discipline, display, rev


def build_catalog(
    rows: Dict[str, Dict[str, List[Tuple[str, str, str]]]],
    out_path: Path,
    preview_dir: Path,
) -> None:
    """Write grouped rows to `out_path`.

    rows structure: {project: {discipline: [(stem, display, rev), ...]}}
    """
    lines: List[str] = []
    lines.append("# Drawing Catalog\n")

    # Small README / usage notes
    lines.append(
        "This file is an auto-generated index of drawings with clickable previews.\n"
    )
    lines.append(
        "- Columns: Drawing (file stem) | Revision (if in filename) | Preview (click thumbnail for full image)\n"
    )
    lines.append("- Preview images are stored in the `Drawings/Previews/` folder.\n")
    lines.append(f"Generated: {datetime.utcnow().isoformat()} UTC\n")

    total = sum(len(v) for d in rows.values() for v in d.values())
    lines.append(f"Summary: {total} drawing{'s' if total != 1 else ''}\n")

    if not rows:
        lines.append("(no drawings found)\n")

    # Friendly project name mapping (extend as needed)
    project_map = {
        "ARCH": "Architectural",
        "MECH": "Mechanical",
        "ELEC": "Electrical",
        "PLUMB": "Plumbing",
        "CAF": "CAF Lab",
    }

    for project in sorted(rows.keys(), key=lambda s: s.lower()):
        # Display a friendly name when available
        disp = project_map.get(project.upper(), project.replace("_", " ").title())
        # compute project counts
        proj_count = sum(len(v) for v in rows[project].values())
        lines.append(
            f"## {disp} ({proj_count} drawing{'s' if proj_count != 1 else ''})\n"
        )
        disciplines = rows[project]
        for disc in sorted(disciplines.keys(), key=lambda s: s.lower()):
            disc_count = len(disciplines[disc])
            lines.append(
                f"### {disc} ({disc_count} drawing{'s' if disc_count != 1 else ''})\n"
            )
            lines.append("| Drawing | Revision | Preview |")
            lines.append("|---|---:|---|")
            for stem, display, rev in sorted(
                disciplines[disc], key=lambda t: t[0].lower()
            ):
                thumb_path = preview_dir / (stem + ".thumb.png")
                full_path = preview_dir / (stem + ".png")
                preview_tag = ""
                if thumb_path.exists():
                    try:
                        thumb_rel = str(
                            Path(thumb_path).relative_to(out_path.parent)
                        ).replace("\\", "/")
                    except Exception:
                        thumb_rel = str(thumb_path).replace("\\", "/")
                    if full_path.exists():
                        try:
                            full_rel = str(
                                Path(full_path).relative_to(out_path.parent)
                            ).replace("\\", "/")
                        except Exception:
                            full_rel = str(full_path).replace("\\", "/")
                        preview_tag = f"[![]({thumb_rel})]({full_rel})"
                    else:
                        preview_tag = f"![]({thumb_rel})"
                elif full_path.exists():
                    try:
                        full_rel = str(
                            Path(full_path).relative_to(out_path.parent)
                        ).replace("\\", "/")
                    except Exception:
                        full_rel = str(full_path).replace("\\", "/")
                    preview_tag = f"![]({full_rel})"
                lines.append(f"| {display} | {rev or ''} | {preview_tag} |")
            lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cad-dir", default="Drawings/CAD")
    parser.add_argument("--preview-dir", default="Drawings/Previews")
    parser.add_argument("--output", default="Drawings/catalog.md")
    args = parser.parse_args()

    cad_dir = Path(args.cad_dir)
    preview_dir = Path(args.preview_dir)
    out_path = Path(args.output)

    cad_files = find_cad_files(cad_dir)

    rows: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    if cad_files:
        for p in cad_files:
            stem = p.stem
            project, discipline, display, rev = parse_name(stem)
            # Normalize discipline name a bit
            discipline = discipline.replace("_", " ").title()
            rows[project][discipline].append((stem, display, rev))
    else:
        # Fallback: scan preview_dir for PNG/thumb files and build entries from their stems
        preview_dir = Path(args.preview_dir)
        if preview_dir.exists():
            preview_files = sorted(
                preview_dir.rglob("*.png"), key=lambda p: p.name.lower()
            )
            seen = set()
            for p in preview_files:
                stem = p.stem
                # skip thumbnail suffix stems like name.thumb
                if stem.endswith(".thumb"):
                    stem = stem[: -len(".thumb")]
                if stem in seen:
                    continue
                seen.add(stem)
                project, discipline, display, rev = parse_name(stem)
                discipline = discipline.replace("_", " ").title()
                rows[project][discipline].append((stem, display, rev))

    preview_dir = Path(args.preview_dir)
    # Ensure preview directory exists (not required, but keep consistent)
    # build the catalog with preview_dir so links are created correctly
    build_catalog(rows, out_path, preview_dir)

    print(f"Wrote catalog to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
