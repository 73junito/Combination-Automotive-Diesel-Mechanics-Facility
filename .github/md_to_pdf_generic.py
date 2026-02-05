#!/usr/bin/env python3
"""Render a simple single-page PDF from a Markdown file.

Usage: python .github/md_to_pdf_generic.py input.md output.pdf
"""

from __future__ import annotations

import pathlib
import sys
from typing import List


def read_lines(path: pathlib.Path) -> List[str]:
    txt = path.read_text(encoding="utf-8")
    return [l.rstrip() for l in txt.splitlines()]


def layout(md_lines: List[str]) -> List[tuple[int, str]]:
    out: List[tuple[int, str]] = []
    for l in md_lines:
        if not l.strip():
            out.append((10, ""))
            continue
        if l.startswith("# "):
            out.append((16, l[2:].strip()))
        elif l.startswith("- [ ") or l.startswith("- [x"):
            out.append((11, "• " + l[2:].strip()))
        elif l.startswith("- "):
            out.append((11, "• " + l[2:].strip()))
        else:
            out.append((10, l.strip()))
    return out


def write_pdf(lines: List[tuple[int, str]], out_path: pathlib.Path) -> None:
    contents = ["BT"]
    y = 740
    current_font = None
    for size, text in lines:
        if text == "":
            y -= 8
            continue
        if current_font != size:
            contents.append(f"/F1 {size} Tf")
            current_font = size
        esc = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        contents.append(f"50 {y} Td ({esc}) Tj")
        y -= int(size * 1.15)
        if y < 40:
            break
    contents.append("ET")
    stream = "\n".join(contents).encode("utf-8") + b"\n"

    objs: List[bytes] = []

    def obj(n: int, data: bytes) -> bytes:
        return f"{n} 0 obj\n".encode() + data + b"\nendobj\n"

    objs.append(obj(1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    objs.append(obj(2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"))
    objs.append(
        obj(
            4,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        )
    )
    page = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
    objs.append(obj(3, page))
    objs.append(
        b"5 0 obj\n<< /Length %d >>\nstream\n" % len(stream)
        + stream
        + b"endstream\nendobj\n"
    )

    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    xrefs = []
    for o in objs:
        xrefs.append(len(pdf))
        pdf += o
    xref_off = len(pdf)
    pdf += b"xref\n0 %d\n" % (len(objs) + 1)
    pdf += b"0000000000 65535 f \n"
    for off in xrefs:
        pdf += b"%010d 00000 n \n" % off
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1,
        xref_off,
    )

    out_path.write_bytes(pdf)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: md_to_pdf_generic.py input.md output.pdf")
        raise SystemExit(2)
    inp = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    lines = read_lines(inp)
    laid = layout(lines)
    write_pdf(laid, out)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
