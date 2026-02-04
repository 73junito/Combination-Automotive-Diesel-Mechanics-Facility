import sys
from pathlib import Path

from PIL import Image

p = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path(__file__).parent / "outputs" / "facility_layout_blender.png"
)
if not p.exists():
    print("MISSING", p)
    raise SystemExit(2)
im = Image.open(p)
print("PATH:", p)
print("SIZE:", im.size)
print("MODE:", im.mode)
print("FORMAT:", im.format)
