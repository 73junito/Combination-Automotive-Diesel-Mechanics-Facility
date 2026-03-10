#!/usr/bin/env python3
"""Generate PNG previews from exported PDFs in Drawings/Exports/PDFs.

The script searches for PDF files under `Drawings/Exports/PDFs/` and converts the first
page of each PDF to a PNG saved in `Drawings/Previews/` with the same stem.

Requires `pdftoppm` (from poppler-utils) or `magick` (ImageMagick) available on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_DIR = REPO_ROOT / "Drawings" / "Exports" / "PDFs"
DEFAULT_PREVIEW_DIR = REPO_ROOT / "Drawings" / "Previews"


def find_pdfs(root: Path):
    if not root.exists():
        return []
    return list(root.rglob("*.pdf"))


def ensure_preview_dir(preview_dir: Path):
    preview_dir.mkdir(parents=True, exist_ok=True)


def convert_pdf_to_png(pdf: Path, out_png: Path) -> int:
    # Try pdftoppm first
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        out_prefix = str(out_png.with_suffix(""))
        cmd = [pdftoppm, "-singlefile", "-png", str(pdf), out_prefix]
        try:
            subprocess.run(cmd, check=True)
            return 0
        except subprocess.CalledProcessError:
            return 2

    # Fallback to ImageMagick 'magick' or 'convert'
    def find_imagemagick():
        # Prefer 'magick' executable (ImageMagick 7+). Avoid Windows' built-in 'convert'.
        path = shutil.which("magick")
        if path:
            return path
        path = shutil.which("convert")
        if not path:
            return None
        # On Windows, the system 'convert' is not ImageMagick (it's in System32). Try to detect ImageMagick by probing --version.
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True)
            if "ImageMagick" in (out.stdout or out.stderr):
                return path
        except Exception:
            pass
        return None

    magick = find_imagemagick()
    if magick:
        # Use density for reasonable resolution
        cmd = [magick, "-density", "150", f"{str(pdf)}[0]", str(out_png)]
        try:
            subprocess.run(cmd, check=True)
            return 0
        except subprocess.CalledProcessError:
            return 3

    # Try a pure-Python fallback using PyMuPDF (fits) if available
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf))
        page = doc.load_page(0)
        mat = fitz.Matrix(2, 2)  # scale for better resolution
        pix = page.get_pixmap(matrix=mat)
        pix.save(str(out_png))
        return 0
    except Exception:
        # If PyMuPDF not available or fails, fall through
        pass

    print(
        "Error: neither 'pdftoppm' nor 'magick'/'convert' found on PATH. Install poppler-utils or ImageMagick."
    )
    return 1


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf-dir",
        action="append",
        default=[str(DEFAULT_PDF_DIR)],
        help="PDF directory to scan (can be repeated)",
    )
    parser.add_argument(
        "--preview-dir",
        default=str(DEFAULT_PREVIEW_DIR),
        help="Preview output directory",
    )
    args = parser.parse_args()

    pdf_dirs = [Path(p) for p in args.pdf_dir]
    preview_dir = Path(args.preview_dir)

    # collect PDFs from all provided dirs
    pdfs = []
    for d in pdf_dirs:
        pdfs.extend(find_pdfs(d))

    if not pdfs:
        print(f"No PDFs found under {[str(d) for d in pdf_dirs]}; nothing to preview.")
        return 0
    ensure_preview_dir(preview_dir)
    failed = False
    generated = []
    for pdf in sorted(pdfs, key=lambda p: p.name.lower()):
        out_png = preview_dir / (pdf.stem + ".png")
        rc = convert_pdf_to_png(pdf, out_png)
        if rc == 0:
            generated.append(out_png)
            print(f"Generated preview: {out_png}")
            # Create thumbnail (max 600px) using ImageMagick if available
            thumb = preview_dir / (pdf.stem + ".thumb.png")
            # Try Pillow first for thumbnailing
            try:
                from PIL import Image

                im = Image.open(out_png)
                im.thumbnail((600, 600))
                im.save(thumb)
                print(f"Generated thumbnail: {thumb}")
            except Exception:
                magick = find_imagemagick()
                if magick:
                    try:
                        subprocess.run(
                            [magick, str(out_png), "-resize", "600x600>", str(thumb)],
                            check=True,
                        )
                        print(f"Generated thumbnail: {thumb}")
                    except subprocess.CalledProcessError:
                        print(f"Failed to generate thumbnail for {out_png}")
                else:
                    print("ImageMagick/Pillow not found; skipping thumbnail generation")
        else:
            print(f"Failed to generate preview for {pdf} (rc={rc})")
            failed = True

    if failed:
        print("Some previews failed to generate.")
        return 2
    print(f"Generated {len(generated)} preview(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
