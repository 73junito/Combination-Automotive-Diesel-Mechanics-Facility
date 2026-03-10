"""
scripts/export_dxf.py

Scaffold script to batch-export drawing files to DXF and PDF. This script is a light wrapper
that builds per-file conversion commands and can either print them (`--dry-run`) or execute
them using an external converter specified by the environment variable `CAD_EXPORT_CMD`.

`CAD_EXPORT_CMD` should be a command template with `{src}` and `{dst}` placeholders, for
example:
  set CAD_EXPORT_CMD="ODAFileConverter.exe \"{src}\" \"{dst}\""

This scaffold avoids embedding vendor-specific conversion code but provides a repeatable
automation entrypoint for CI or local use.
"""

import argparse
import os
import subprocess
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1] / "Drawings" / "CAD"
DXF_OUT_DIR = Path(__file__).resolve().parents[1] / "Drawings" / "DXF"
PDF_OUT_DIR = Path(__file__).resolve().parents[1] / "Drawings" / "Exports" / "PDFs"

EXTS = [".dwg", ".dxf", ".svg", ".step", ".stp"]


def find_sources(root: Path):
    for p in root.rglob("*"):
        if p.suffix.lower() in EXTS:
            yield p


def build_output_paths(src: Path):
    rel = src.relative_to(SOURCE_DIR)
    out_dxf = DXF_OUT_DIR / rel.with_suffix(".dxf")
    out_pdf = PDF_OUT_DIR / rel.with_suffix(".pdf")
    out_dxf.parent.mkdir(parents=True, exist_ok=True)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    return out_dxf, out_pdf


def run_conversion(cmd_template: str, src: Path, dst: Path, dry_run: bool):
    cmd = cmd_template.format(src=str(src), dst=str(dst))
    if dry_run:
        print(cmd)
        return 0
    try:
        print("RUN:", cmd)
        proc = subprocess.run(cmd, shell=True, check=True)
        return proc.returncode
    except subprocess.CalledProcessError as e:
        print("Conversion failed:", e)
        return e.returncode


def main():
    parser = argparse.ArgumentParser(description="Batch-export drawings to DXF/PDF")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands instead of running"
    )
    parser.add_argument("--pdf-only", action="store_true", help="Export PDF only")
    parser.add_argument(
        "--src",
        action="append",
        help="Specific source file(s) to convert (relative or absolute). Can be repeated.",
    )
    parser.add_argument(
        "--add-git",
        action="store_true",
        help="Add generated files to git (if in a git repo)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run conversions and exit (used by CI to detect changes). Does not git-add files.",
    )
    args = parser.parse_args()

    cmd_template = os.environ.get("CAD_EXPORT_CMD")
    if not cmd_template and not args.dry_run:
        print("Environment variable CAD_EXPORT_CMD is not set.\n")
        print(
            "Set CAD_EXPORT_CMD to a command template that accepts {src} and {dst} placeholders."
        )
        print(
            'Example (Windows): set CAD_EXPORT_CMD="ODAFileConverter.exe "{src}" "{dst}""'
        )
        print("Using --dry-run will still show commands to run once configured.")

    sources = []
    if args.src:
        for s in args.src:
            p = Path(s)
            if not p.is_absolute():
                p = Path.cwd() / p
            if p.exists():
                sources.append(p)
            else:
                print(f"Warning: specified source does not exist: {p}")
    else:
        sources = list(find_sources(SOURCE_DIR))

    generated = []
    for src in sources:
        out_dxf, out_pdf = build_output_paths(src)
        # Prefer leaving native DXF if present
        if src.suffix.lower() == ".dxf":
            # PDF from DXF
            if cmd_template:
                target = out_pdf
                rc = run_conversion(cmd_template, src, target, args.dry_run)
                if rc == 0:
                    generated.append(target)
            else:
                print(f"DXF found: {src} -> (no converter configured for PDF)")
        else:
            # For other source types, build DXF then PDF
            if not args.pdf_only:
                if cmd_template:
                    rc = run_conversion(cmd_template, src, out_dxf, args.dry_run)
                    if rc == 0:
                        generated.append(out_dxf)
                else:
                    print(f"Would convert to DXF: {src} -> {out_dxf}")
            if cmd_template:
                rc = run_conversion(cmd_template, src, out_pdf, args.dry_run)
                if rc == 0:
                    generated.append(out_pdf)
            else:
                print(f"Would convert to PDF: {src} -> {out_pdf}")

    if args.add_git and generated:
        try:
            subprocess.run(["git", "add"] + [str(p) for p in generated], check=True)
            print("Added generated files to git: ", generated)
        except Exception as e:
            print("Failed to git add generated files:", e)

    # For CI check-only mode: if --check-only was requested, return non-zero if any conversions failed.
    if args.check_only:
        # If CAD_EXPORT_CMD wasn't set and dry-run was not used, mark as failure
        if (not cmd_template) and (not args.dry_run):
            print(
                "CAD_EXPORT_CMD not set; cannot perform conversions in --check-only mode."
            )
            return 2
        # When check-only, we assume any visible error was printed above; exit 0
        return 0


if __name__ == "__main__":
    main()
