import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional, cast

# annotate pypdf types for mypy
PdfReader: Optional[Any] = None
PdfReadError: Optional[Any] = None
PYPDF_AVAILABLE = False
try:
    from pypdf import PdfReader as _PdfReader

    PdfReader = _PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF_AVAILABLE = False

# Try to import a specific PDF read error class if pypdf is available
if PYPDF_AVAILABLE:
    try:
        from pypdf.errors import PdfReadError as _PdfReadError

        PdfReadError = _PdfReadError
    except ImportError:
        PdfReadError = None

PDF_KEY_FIELDS = [
    ("project", re.compile(r"project", re.I)),
    ("author", re.compile(r"author", re.I)),
    ("sheet", re.compile(r"sheet", re.I)),
    ("date", re.compile(r"date", re.I)),
    ("revision", re.compile(r"revision", re.I)),
    ("scale_text", re.compile(r"scale|1:", re.I)),
    ("north", re.compile(r"north", re.I)),
    ("legend", re.compile(r"legend|symbol", re.I)),
]

REQUIRED_LAYERS = [
    "FLOOR",
    "WALLS",
    "EQUIPMENT",
    "ELECTRICAL",
    "HVAC",
    "PLUMBING",
    "AIR_GAS",
    "AUTO_BAYS",
    "DIESEL_BAYS",
]

EQUIP_KEYWORDS = {
    "EQUIPMENT": ["lift", "compressor", "welder", "scanner", "hoist"],
    "ELECTRICAL": ["panel", "receptacle", "lighting", "fixture", "ckt", "circuit"],
    "HVAC": ["exhaust", "hood", "diffuser", "duct", "cfm"],
    "PLUMBING": ["drain", "sink", "floor drain", "trap"],
    "AIR_GAS": ["air", "compressor", "air drop", "gas"],
    "AUTO_BAYS": ["bay", "service bay"],
    "DIESEL_BAYS": ["diesel", "diesel hood", "diesel bay"],
}


def extract_pdf_text(pdf_path: Path) -> str:
    if not PYPDF_AVAILABLE:
        raise RuntimeError(
            "pypdf (install with: pip install pypdf) is required to extract PDF text"
        )
    # PdfReader is Optional[Any] at module scope; narrow for mypy before calling
    Reader = cast(Any, PdfReader)
    reader = Reader(str(pdf_path))
    text = []
    for p in reader.pages[:6]:
        try:
            t = p.extract_text()
        except (AttributeError, ValueError):
            t = None
        if t:
            text.append(t)
    return "\n".join(text)


def check_pdf_fields(text: str):
    results = {}
    for key, rx in PDF_KEY_FIELDS:
        results[key] = bool(rx.search(text))
    return results


def check_layers_in_dxf(dxf_path: Path):
    text = dxf_path.read_text(encoding="utf-8", errors="ignore")
    found = {}
    for layer in REQUIRED_LAYERS:
        # accept either exact name or with common separators
        found[layer] = bool(re.search(r"\b" + re.escape(layer) + r"\b", text, re.I))
    # search for header vars
    found_meta = {
        "REALWORLDSCALE": ("$REALWORLDSCALE" in text) or ("REALWORLDSCALE" in text),
        "NORTHDIRECTION": ("$NORTHDIRECTION" in text) or ("NORTHDIRECTION" in text),
    }
    # heuristic: collect layer names from TABLES section by extracting group-code 2 entries
    layer_names = set()
    for m in re.finditer(r"\n\s*2\s*\n\s*([A-Za-z0-9_\-\s]+)\s*\n", text):
        name = m.group(1).strip()
        if name:
            layer_names.add(name)
    # fallback: basic scanning for layer-like tokens after 'LAYER' keywords
    for m in re.finditer(r"LAYER[\s\S]{0,80}?2\s*\n\s*([A-Za-z0-9_\-]+)", text, re.I):
        layer_names.add(m.group(1))
    return found, found_meta, sorted(layer_names)


def spot_check_labels(text: str):
    res = {}
    lower = text.lower()
    for layer, keywords in EQUIP_KEYWORDS.items():
        hits = []
        for kw in keywords:
            if kw.lower() in lower:
                hits.append(kw)
        res[layer] = hits[:5]
    return res


EXIT_OK = 0
# Validation failures (e.g., PDF/DXF content problems)
EXIT_VALIDATION = 1
# Input error (missing files / invalid file paths)
EXIT_INPUT = 2
# Missing dependency (optional runtime dependency not installed)
EXIT_DEP_MISSING = 3


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="auto_drawing_check.py",
        description="Quickly check PDFs and DXF layouts for expected fields and layers",
    )
    parser.add_argument("pdf", help="Path to portfolio PDF")
    parser.add_argument("dxf", help="Path to layout DXF")
    parser.add_argument("--out", "-o", help="Write JSON result to file")
    parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default="WARN",
        help="Logging level for informational output (default: WARN)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing input files as errors (exit with EXIT_INPUT)",
    )
    args = parser.parse_args(argv)

    # Configure logging to stderr; keep JSON on stdout
    numeric_level = getattr(logging, args.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("auto_drawing_check")

    pdf_path = Path(args.pdf)
    dxf_path = Path(args.dxf)

    out: dict[str, Any] = {}
    out["pdf_exists"] = pdf_path.exists()
    out["dxf_exists"] = dxf_path.exists()

    # In strict mode, treat missing inputs as immediate errors for CI/validation.
    if args.strict:
        missing = []
        if not out["pdf_exists"]:
            missing.append("PDF not found: {}".format(pdf_path))
        if not out["dxf_exists"]:
            missing.append("DXF not found: {}".format(dxf_path))
        if missing:
            for m in missing:
                logger.error(m)
            return EXIT_INPUT
    else:
        # Non-strict (default): warn about missing inputs but continue and emit JSON.
        if not out["pdf_exists"]:
            logger.warning("PDF not found: %s", pdf_path)
        if not out["dxf_exists"]:
            logger.warning("DXF not found: %s", dxf_path)

    if out["pdf_exists"]:
        # If pypdf isn't available, surface a clear exit code for missing dependency.
        if not PYPDF_AVAILABLE:
            logger.error(
                "pypdf is required to extract PDF text. Install with: pip install pypdf"
            )
            return EXIT_DEP_MISSING
        # Extraction can fail due to file I/O or PDF read errors
        try:
            text = extract_pdf_text(pdf_path)
        except Exception as e:
            # Could be PdfReadError, OSError, or other parsing error; log and treat as validation failure
            logger.error("failed extracting PDF text: %s", e)
            return EXIT_VALIDATION
        out["pdf_text_snippet"] = text[:1200]
        out["pdf_fields"] = check_pdf_fields(text)
        out["label_spot_checks"] = spot_check_labels(text)
    else:
        out["pdf_fields"] = {}
        out["label_spot_checks"] = {}

    if out["dxf_exists"]:
        try:
            layers_found, meta_found, layer_names = check_layers_in_dxf(dxf_path)
            out["layers_found"] = layers_found
            out["header_meta"] = meta_found
            out["layer_names_sample"] = layer_names[:200]
        except (OSError, UnicodeDecodeError) as e:
            out["layers_error"] = str(e)
            logger.error("failed reading DXF for layers: %s", e)

    import json

    dump = json.dumps(out, indent=2)

    if args.out:
        try:
            Path(args.out).write_text(dump, encoding="utf-8")
            logger.info("Wrote results to %s", args.out)
        except OSError as e:
            logger.error("failed to write output file: %s", e)
            return EXIT_VALIDATION
    else:
        # Keep JSON output on stdout so pipelines can consume it; logs go to stderr.
        print("---AUTO_DRAWING_CHECK_RESULT---")
        print(dump)

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
