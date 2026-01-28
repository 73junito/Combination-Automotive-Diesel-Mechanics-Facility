import sys
from pathlib import Path
from xml.etree import ElementTree as ET

svg_path = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path(__file__).parent / "outputs" / "facility_layout_fallback.svg"
)
if not svg_path.exists():
    print("MISSING", svg_path)
    raise SystemExit(2)

ns = {"svg": "http://www.w3.org/2000/svg"}
tree = ET.parse(svg_path)
root = tree.getroot()

texts = []
for el in root.iter():
    tag = el.tag
    if tag.endswith("}text") or tag == "text":
        txt = "".join(el.itertext()).strip()
        if txt:
            texts.append(txt)

print("SVG PATH:", svg_path)
print("EXTRACTED TEXT SNIPPET:")
for t in texts[:200]:
    print("-", t)

keywords = ["project", "author", "sheet", "date", "revision", "scale", "north", "legend"]
found = {k: any(k in s.lower() for s in texts) for k in keywords}
print("\nKEYWORD PRESENCE:")
for k, v in found.items():
    print(f"{k}: {v}")
