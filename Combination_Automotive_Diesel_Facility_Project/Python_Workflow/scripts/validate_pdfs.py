#!/usr/bin/env python3
import os
import re
from pathlib import Path

OUT = Path(__file__).parent / "outputs"
files = {
    "essential": OUT / "Essential_Equipment_Cost_List.pdf",
    "nonessential": OUT / "Nonessential_Equipment_Cost_List.pdf",
    "furniture": OUT / "Furniture_List_with_Cost.pdf",
    "maintenance": OUT / "Maintenance_and_Replacement_Costs.pdf",
    "total": OUT / "Total_Facility_Cost_Estimate.pdf",
}


def extract_text(pdf_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf missing")
        return None
    try:
        reader = PdfReader(str(pdf_path))
        texts = []
        for p in reader.pages[:3]:
            texts.append(p.extract_text() or "")
        return "\n".join(texts)
    except Exception as e:
        return f"ERROR: {e}"


def check_pdf(name, path):
    exists = path.exists()
    print(f"--- {name} ---")
    print(f"path: {path}")
    print(f"exists: {exists}")
    if not exists:
        return
    text = extract_text(path)
    if text is None:
        print("Could not extract text (pypdf missing)")
        return
    if text.startswith("ERROR:"):
        print(text)
        return
    snippet = text.strip().split("\n")[:20]
    print("--- Text snippet (first lines) ---")
    for line in snippet:
        print(line)
    # checks
    has_title = bool(
        re.search(
            r"Essential|Nonessential|Furniture|Maintenance|Total", text, re.IGNORECASE
        )
    )
    has_columns = bool(
        re.search(r"Item\s+Qty|Quantity|Unit Cost|Total", text, re.IGNORECASE)
    )
    has_currency = bool(re.search(r"\$\s*\d|\d,\d{3}", text))
    has_subtotal = bool(
        re.search(
            r"Subtotal|Total Facility|Grand total|Grand Total", text, re.IGNORECASE
        )
    )
    print(
        "has_title:",
        has_title,
        "has_columns:",
        has_columns,
        "has_currency:",
        has_currency,
        "has_subtotal:",
        has_subtotal,
    )


def main():
    for k, p in files.items():
        check_pdf(k, p)


if __name__ == "__main__":
    main()
