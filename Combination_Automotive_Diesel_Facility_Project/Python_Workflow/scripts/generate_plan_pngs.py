from pathlib import Path
import cairosvg
from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPTS_DIR

SVG_GLOB = "facility_*.svg"

def svg_to_png(svg_path: Path, png_path: Path):
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))

def make_thumbnail(png_path: Path, thumb_path: Path, max_size=(420, 240)):
    with Image.open(png_path) as im:
        im.thumbnail(max_size)
        im.save(thumb_path, format="PNG")

def main():
    svgs = sorted(SCRIPTS_DIR.glob(SVG_GLOB))
    if not svgs:
        print("No SVGs found to convert.")
        return

    for svg in svgs:
        name = svg.stem
        png = OUT_DIR / f"{name}.png"
        thumb = OUT_DIR / f"{name}.thumb.png"
        print(f"Converting {svg.name} -> {png.name}")
        svg_to_png(svg, png)
        print(f"Creating thumbnail {thumb.name}")
        make_thumbnail(png, thumb)

    print("All conversions complete.")

if __name__ == "__main__":
    main()
