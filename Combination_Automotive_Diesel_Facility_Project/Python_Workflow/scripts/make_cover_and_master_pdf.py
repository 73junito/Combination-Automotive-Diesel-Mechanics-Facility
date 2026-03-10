#!/usr/bin/env python3
"""
Create a simple cover page PDF and convert an existing master PNG to a PDF.

Usage:
  python make_cover_and_master_pdf.py --png <master_png> --out-dir <outdir> --name "Your Name"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt


def make_cover(
    out_path: Path,
    title: str,
    name: str,
    course: str,
    purpose: str,
    thumbnail_path: Path | None,
):
    fig = plt.figure(figsize=(8.5, 11))  # letter portrait
    ax = fig.add_subplot(111)
    ax.axis("off")

    ax.text(0.5, 0.85, title, fontsize=28, ha="center", va="center", weight="bold")
    ax.text(0.5, 0.76, name, fontsize=14, ha="center")
    ax.text(0.5, 0.73, course, fontsize=12, ha="center")
    ax.text(0.5, 0.68, purpose, fontsize=10, ha="center")

    if thumbnail_path and thumbnail_path.exists():
        img = mpimg.imread(str(thumbnail_path))
        # place thumbnail lower center
        ax_img = fig.add_axes([0.15, 0.08, 0.7, 0.45])
        ax_img.imshow(img)
        ax_img.axis("off")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), bbox_inches="tight")
    plt.close(fig)


def make_master_pdf(png_path: Path, out_path: Path):
    img = mpimg.imread(str(png_path))
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.axis("off")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--png", required=True, help="Master PNG to convert")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--name", default="Author Name")
    p.add_argument("--course", default="TTED 719")
    p.add_argument(
        "--purpose", default="Facility Portfolio — administrator/advisory-ready"
    )
    args = p.parse_args()

    png = Path(args.png)
    outdir = Path(args.out_dir)

    cover_pdf = outdir / "cover_page.pdf"
    master_pdf = outdir / "master_plan.pdf"

    make_cover(
        cover_pdf, "Facility Portfolio", args.name, args.course, args.purpose, png
    )
    make_master_pdf(png, master_pdf)

    print("WROTE:", cover_pdf)
    print("WROTE:", master_pdf)


if __name__ == "__main__":
    main()
