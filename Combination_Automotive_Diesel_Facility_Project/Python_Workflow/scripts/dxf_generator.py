import os
from dataclasses import dataclass
from typing import Any, List, Optional

# annotate module variable so mypy knows this may be None when ezdxf
ezdxf: Optional[Any] = None
try:
    import ezdxf as _ezdxf

    ezdxf = _ezdxf
except ImportError:
    ezdxf = None

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUTPUT_DIR = os.path.normpath(os.path.join(ROOT, "Python_Workflow", "outputs"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Layer names (match project template)
LAYERS = [
    "WALLS",
    "AUTO_BAYS",
    "DIESEL_BAYS",
    "EQUIPMENT",
    "ELECTRICAL",
    "PLUMBING",
    "AIR_GAS",
    "HVAC",
    "SAFETY",
    "TRAFFIC_FLOW",
    "TEXT_LABELS",
]


@dataclass
class Bay:
    x: float
    y: float
    width: float
    depth: float
    layer: str
    name: str = ""


@dataclass
class EquipmentItem:
    x: float
    y: float
    w: float
    h: float
    layer: str
    name: str = ""


def create_dxf_document(filename: str = "facility_layout.dxf") -> str:
    """Create a DXF document and write a minimal layout. Returns output path."""
    if ezdxf is None:
        raise RuntimeError("ezdxf is not installed. Install via pip install ezdxf")

    # Guard: do not emit placeholder equipment when building for a release/CI.
    # Set environment variable RELEASE_BUILD=1 to enable strict release mode.
    def is_release_build() -> bool:
        return os.getenv("RELEASE_BUILD") == "1" or os.getenv("CI") is not None

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Ensure layers exist
    for layer in LAYERS:
        if layer not in doc.layers:
            doc.layers.new(name=layer)

    # Example: add outer walls rectangle on WALLS layer
    add_rectangle(msp, 0, 0, 200, 120, layer="WALLS", lw=0.5)

    # Example parametric layout: add 8 automotive bays
    auto_bays = generate_bays(
        start_x=5, start_y=5, count=8, bay_w=22, bay_d=40, spacing=2, layer="AUTO_BAYS"
    )
    for bay in auto_bays:
        add_rectangle(msp, bay.x, bay.y, bay.width, bay.depth, layer=bay.layer)
        add_text(
            msp,
            bay.name or "Auto Bay",
            bay.x + 1,
            bay.y + bay.depth - 4,
            layer="TEXT_LABELS",
        )

    # Example diesel bays (4 oversized)
    diesel_bays = generate_bays(
        start_x=5,
        start_y=55,
        count=4,
        bay_w=30,
        bay_d=60,
        spacing=4,
        layer="DIESEL_BAYS",
    )
    for bay in diesel_bays:
        add_rectangle(msp, bay.x, bay.y, bay.width, bay.depth, layer=bay.layer)
        add_text(
            msp,
            bay.name or "Diesel Bay",
            bay.x + 1,
            bay.y + bay.depth - 6,
            layer="TEXT_LABELS",
        )

    # TODO: replace placeholder equipment with real definitions
    # In release builds (RELEASE_BUILD=1 or CI env var present) abort rather than
    # emitting DXFs that contain placeholder equipment.
    if is_release_build():
        raise RuntimeError(
            "Release build: placeholder equipment would be emitted; aborting DXF generation"
        )

    # Development/sample placeholder equipment (will not be created in release builds)
    add_rectangle(msp, 150, 10, 10, 6, layer="EQUIPMENT")
    add_text(msp, "Tool Room", 150, 9, layer="TEXT_LABELS")

    out_path = os.path.join(OUTPUT_DIR, filename)
    doc.saveas(out_path)
    return out_path


def add_rectangle(
    msp, x: float, y: float, w: float, h: float, layer: str = "0", lw: float = 0.2
):
    """Add a rectangle as a lightweight polyline on `layer`."""
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    msp.add_lwpolyline(points, dxfattribs={"layer": layer, "closed": True})


def add_text(msp, text: str, x: float, y: float, layer: str = "0", height: float = 2.5):
    tx = msp.add_text(text, dxfattribs={"layer": layer, "height": height})
    # set insertion point directly for compatibility across ezdxf versions
    tx.dxf.insert = (x, y)


def generate_bays(
    start_x: float,
    start_y: float,
    count: int,
    bay_w: float,
    bay_d: float,
    spacing: float,
    layer: str,
) -> List[Bay]:
    bays = []
    x = start_x
    y = start_y
    for i in range(count):
        bays.append(
            Bay(
                x=x, y=y, width=bay_w, depth=bay_d, layer=layer, name=f"{layer}_{i + 1}"
            )
        )
        x += bay_w + spacing
    return bays


def main():
    # Minimal runner: will raise if ezdxf missing
    try:
        out = create_dxf_document("facility_layout_sample.dxf")
        print(f"DXF written to: {out}")
    except Exception as e:
        print("Failed to create DXF:", e)


if __name__ == "__main__":
    main()
