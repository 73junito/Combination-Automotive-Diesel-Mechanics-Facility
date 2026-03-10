#!/usr/bin/env python3
"""Pre-commit checks for Drawings files.

Checks performed:
- Filename validation: no spaces and contains '-DWG' and '_rev'
- Title block presence for text-based sources (SVG/DXF) (warning)
- Project `project-metadata.json` must exist and contain `units` (blocking)
- Optional: warn if exported PDFs are missing or out-of-date

Drop this script into `.git/hooks/pre-commit` (or copy the sample in `.githooks/`).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = REPO_ROOT / "Drawings" / "CAD"
EXPORT_PDF_ROOT = REPO_ROOT / "Drawings" / "Exports" / "PDFs"

SOURCE_EXTS = {".dwg", ".dxf", ".svg", ".step", ".stp", ".cdl", ".cqx"}

# Strict filename regex (case-insensitive)
# Example: PROJECT-AREA-ROLE-DWG001_rev01.dwg
FILENAME_REGEX = re.compile(
    r"^[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-DWG\d{3}_rev\d{2}\\.(dwg|cdl|cqx)$", re.IGNORECASE
)


def get_staged_files() -> list[Path]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    if out.returncode != 0:
        print("Failed to run git diff --cached --name-only", file=sys.stderr)
        return []
    names = [s.strip() for s in out.stdout.splitlines() if s.strip()]
    return [Path(n) for n in names]


def is_cad_file(p: Path) -> bool:
    return (
        p.suffix.lower() in SOURCE_EXTS
        and Path(p).parts
        and "Drawings" in Path(p).parts
    )


def check_filename(p: Path) -> bool:
    name = p.name
    if " " in name:
        print(f"ERROR: Filename contains spaces: {p}")
        return False
    if not FILENAME_REGEX.match(name):
        print(
            f"ERROR: Filename does not match required pattern: {name}\n  Expected: PROJECT-AREA-ROLE-DWG###_rev##.ext"
        )
        return False
    return True


def find_project_metadata(start: Path) -> Path | None:
    cur = start.resolve()
    for parent in [cur] + list(cur.parents):
        candidate = parent / "project-metadata.json"
        if candidate.exists():
            return candidate
        # also check Drawings root for a top-level metadata file
        if parent == REPO_ROOT:
            top = REPO_ROOT / "Drawings" / "project-metadata.json"
            if top.exists():
                return top
    return None


def check_project_units(p: Path) -> bool:
    # Look for project-metadata.json in the file's ancestors
    folder = p.parent
    meta = find_project_metadata(folder)
    if not meta:
        print(
            f"ERROR: project-metadata.json not found for {p}; please add one in the project folder"
        )
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: failed to parse {meta}: {e}")
        return False
    if "units" not in data:
        print(f"ERROR: 'units' key missing in {meta}; add 'units': 'metric'|'imperial'")
        return False
    if data["units"] not in ("metric", "imperial"):
        print(
            f"ERROR: 'units' in {meta} must be exactly 'metric' or 'imperial' (found: {data.get('units')})"
        )
        return False
    return True


def check_title_block(p: Path) -> bool:
    # Enforce title block presence. For text-based sources (SVG/DXF) scan for key tokens.
    # For binary DWG files, require a corresponding exported DXF (in Drawings/DXF) to be present
    # so we can scan it; otherwise fail the commit and ask for a DXF/PDF export for automated checks.
    ext = p.suffix.lower()
    tokens = ("project:", "title-block", "title:")
    if ext in {".svg", ".dxf", ".txt", ".md"}:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            print(f"ERROR: could not read {p} to check title block")
            return False
        lowered = text.lower()
        if any(t in lowered for t in tokens):
            return True
        print(
            f"ERROR: title block not detected in {p} (text scan). Please ensure a title block is present."
        )
        return False
    elif ext == ".dwg":
        # Look for a DXF export in Drawings/DXF with same relative path
        try:
            rel = p.relative_to(REPO_ROOT / "Drawings" / "CAD")
            dxf_equiv = REPO_ROOT / "Drawings" / "DXF" / rel.with_suffix(".dxf")
            if dxf_equiv.exists():
                try:
                    txt = dxf_equiv.read_text(encoding="utf-8", errors="ignore").lower()
                    if any(t in txt for t in tokens):
                        return True
                    print(
                        f"ERROR: title block not detected in DXF equivalent {dxf_equiv} for {p}."
                    )
                    return False
                except Exception:
                    print(
                        f"ERROR: cannot read DXF {dxf_equiv} to verify title block for {p}."
                    )
                    return False
            else:
                print(
                    f"ERROR: DWG {p} has no DXF equivalent at expected {dxf_equiv}. Provide DXF/PDF export for automated title-block checks."
                )
                return False
        except Exception:
            print(
                f"ERROR: failed to determine DXF equivalent for {p}; ensure exports are in Drawings/DXF/"
            )
            return False
    else:
        # For other binary formats, deny until an export exists
        print(f"ERROR: Unsupported source type for automated title-block check: {p}")
        return False


def check_exports_fresh(p: Path) -> bool:
    rel = None
    try:
        rel = p.relative_to(CAD_ROOT)
    except Exception:
        # not under CAD_ROOT
        return True
    pdf = EXPORT_PDF_ROOT / rel.with_suffix(".pdf")
    if not pdf.exists():
        print(f"Export PDF missing for {p} -> expected {pdf}")
        # attempt auto-conversion if possible
        return False
    try:
        if p.stat().st_mtime > pdf.stat().st_mtime:
            print(f"Export PDF older than source for {p} (regenerate PDF)")
            return False
    except Exception:
        print(f"ERROR: failed to compare timestamps for {p} and {pdf}")
        return False
    return True


def main(argv: Iterable[str] | None = None) -> int:
    staged = get_staged_files()
    if not staged:
        return 0

    cad_files = [p for p in staged if is_cad_file(p)]
    if not cad_files:
        # nothing to do
        return 0

    failed = False
    for p in cad_files:
        # only run checks for files that exist in the workspace
        if not p.exists():
            # could be deleted or renamed; skip
            continue
        ok_name = check_filename(p)
        if not ok_name:
            failed = True
        if not check_project_units(p):
            failed = True
        ok_title = check_title_block(p)
        if not ok_title:
            failed = True

        ok_export = check_exports_fresh(p)
        if not ok_export:
            # try auto-conversion using export_dxf.py if CAD_EXPORT_CMD is set
            cad_cmd = os.environ.get("CAD_EXPORT_CMD")
            if cad_cmd:
                print(f"Attempting auto-conversion for {p} using CAD_EXPORT_CMD...")
                try:
                    repo_root = Path(__file__).resolve().parents[1]
                    runner = sys.executable
                    script = repo_root / "scripts" / "export_dxf.py"
                    # pass source path and request git-add
                    proc = subprocess.run(
                        [runner, str(script), "--src", str(p), "--add-git"], check=False
                    )
                    if proc.returncode == 0:
                        print(
                            f"Auto-conversion completed for {p}; re-checking exports..."
                        )
                        ok_export = check_exports_fresh(p)
                        if not ok_export:
                            print(
                                f"ERROR: exports still missing or stale after auto-conversion for {p}"
                            )
                            failed = True
                        else:
                            print(f"Exports are up-to-date for {p}")
                    else:
                        print(
                            f"ERROR: auto-conversion command failed (exit {proc.returncode}) for {p}"
                        )
                        failed = True
                except Exception as e:
                    print(f"ERROR: auto-conversion attempt failed: {e}")
                    failed = True
            else:
                print(
                    "ERROR: CAD_EXPORT_CMD not set; cannot auto-convert missing/stale exports."
                )
                failed = True

    if failed:
        print("\nPre-commit checks failed. Fix the errors and try again.")
        return 1
    print("Pre-commit checks passed (with warnings possibly).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
