#!/usr/bin/env python3
"""Simple Markdown-to-PDF renderer (single-page) with no external deps.

Reads `TTED719_mapping.md` (repo root) and writes `TTED719_mapping.pdf` (repo root).

This is intentionally small and conservative: it lays out lines with simple header sizing.
"""

from __future__ import annotations

import pathlib
import re
from typing import List

IN = pathlib.Path("TTED719_mapping.md")
OUT = pathlib.Path("TTED719_mapping.pdf")


def read_lines() -> List[str]:
    if not IN.exists():
        raise SystemExit(f"Input file not found: {IN}")
    txt = IN.read_text(encoding="utf-8")
    lines = [l.rstrip() for l in txt.splitlines()]
    return lines


def layout_lines(md_lines: List[str]) -> List[tuple[int, str]]:
    # return list of (font_size, text)
    out = []
    for l in md_lines:
        if not l:
            out.append((10, ""))
            continue
        if l.startswith("# "):
            out.append((16, l[2:].strip()))
        elif l.startswith("- **") and l.endswith(":"):
            # bullet header
            out.append((12, "• " + re.sub(r"^- \*\*(.+)\*\*:", r"\1:", l)))
        elif l.startswith("- "):
            out.append((11, "• " + l[2:].strip()))
        elif l.startswith("+ "):
            out.append((11, l[2:].strip()))
        else:
            out.append((10, l.strip()))
    return out


def write_pdf(lines: List[tuple[int, str]]) -> None:
    # Minimal PDF generation using builtin Type1 font Helvetica
    # Page size: US Letter 612 x 792 pts
    contents = []
    contents.append("BT")
    y = 740
    last_size = None
    for size, text in lines:
        if text == "":
            y -= 8
            continue
        if last_size != size:
            contents.append(f"/{'F1'} {size} Tf")
            last_size = size
        # escape parentheses
        esc = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        contents.append(f"50 {y} Td ({esc}) Tj")
        y -= int(size * 1.2)
        if y < 40:
            break
    contents.append("ET")
    stream = "\n".join(contents) + "\n"

    # Build PDF objects
    objs: List[bytes] = []

    def obj(n: int, data: bytes) -> bytes:
        return f"{n} 0 obj\n".encode() + data + b"\nendobj\n"

    # 1 Catalog
    objs.append(obj(1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    # 2 Pages
    objs.append(obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"))
    # 3 Page
    contents_bytes = stream.encode("utf-8")
    # 4 Font
    objs.append(
        obj(
            4,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        )
    )
    # 5 Content stream placeholder (length to fill)
    # 3 refers to resources that include the font and contents
    page_dict = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode()
    objs.append(obj(3, page_dict))
    objs.append(
        b"5 0 obj\n<< /Length %d >>\nstream\n" % len(contents_bytes)
        + contents_bytes
        + b"endstream\nendobj\n"
    )

    # write file with xref
    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    xref = []
    for o in objs:
        xref.append(len(pdf))
        pdf += o
    xref_tab_offset = len(pdf)
    # xref
    xref_header = b"xref\n0 %d\n" % (len(objs) + 1)
    pdf += xref_header
    pdf += b"0000000000 65535 f \n"
    for off in xref:
        pdf += b"%010d 00000 n \n" % off
    # trailer
    trailer = b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1,
        xref_tab_offset,
    )
    pdf += trailer

    OUT.write_bytes(pdf)
    print(f"Wrote {OUT} ({len(pdf)} bytes)")


def main() -> None:
    md_lines = read_lines()
    laid = layout_lines(md_lines)
    write_pdf(laid)


if __name__ == "__main__":
    main()
