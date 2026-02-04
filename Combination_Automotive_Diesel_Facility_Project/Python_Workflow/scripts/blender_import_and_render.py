"""
Blender automation script to import an SVG, center/scale it, label it, and render a PNG.
Run from command line with Blender (headless):

blender --background --python blender_import_and_render.py -- input.svg output.png [--scale 1.0] [--res 3840 2160] [--apply-scale]

Arguments after "--":
  input.svg        Path to the SVG to import
  output.png       Path for the rendered PNG
  --scale <f>      Optional uniform scale multiplier (default: auto-fit)
  --res <x> <y>    Optional render resolution (default: 1920 1080)
  --apply-scale    Apply scale (Ctrl+A) before rendering

Notes:
- Requires Blender's SVG import add-on (script will try to enable it).
- Script creates a camera and light, centers the imported curve(s), sets object name to
  'Engineering_Layout_Reference', and adds a small text note.
"""

import os
import sys

import bpy
from mathutils import Vector

# Parse args after --
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1 :]
else:
    argv = []

if len(argv) < 2:
    print(
        "Usage: blender --background --python blender_import_and_render.py -- input.svg output.png [--scale 1.0] [--res 1920 1080] [--apply-scale]"
    )
    sys.exit(1)

input_svg = os.path.abspath(argv[0])
output_png = os.path.abspath(argv[1])

# defaults
scale_arg = None
res_x, res_y = 1920, 1080
apply_scale = False

i = 2
while i < len(argv):
    a = argv[i]
    if a == "--scale" and i + 1 < len(argv):
        scale_arg = float(argv[i + 1])
        i += 2
    elif a == "--res" and i + 2 < len(argv):
        res_x = int(argv[i + 1])
        res_y = int(argv[i + 2])
        i += 3
    elif a == "--apply-scale":
        apply_scale = True
        i += 1
    else:
        i += 1

print("Input SVG:", input_svg)
print("Output PNG:", output_png)
print(
    "Scale arg:",
    scale_arg,
    "Resolution:",
    res_x,
    "x",
    res_y,
    "Apply scale:",
    apply_scale,
)

# Enable SVG importer addon if available
try:
    bpy.ops.wm.addon_enable(module="io_curve_svg")
    print("SVG importer addon enabled (io_curve_svg).")
except RuntimeError:
    try:
        bpy.ops.wm.addon_enable(module="io_import_curve_svg")
        print("SVG importer addon enabled (io_import_curve_svg).")
    except RuntimeError:
        print(
            'Could not ensure SVG importer add-on is enabled; if import fails, enable "Import-Export: Scalable Vector Graphics (SVG)" in Preferences.'
        )

# Clean default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import SVG
if not os.path.exists(input_svg):
    print("SVG not found:", input_svg)
    sys.exit(2)

try:
    bpy.ops.import_curve.svg(filepath=input_svg)
except RuntimeError as e:
    print("SVG import failed:", e)
    sys.exit(3)

# Collect imported objects (curves)
# prefer actual geometry types; SVG importer may create EMPTY parents
imported = [obj for obj in bpy.context.scene.objects if obj.type in ("CURVE", "MESH")]
if not imported:
    print("No objects imported from SVG.")
    sys.exit(4)

# Select imported curve objects
for obj in bpy.context.scene.objects:
    obj.select_set(False)
for obj in imported:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

# Join into single object if multiple curves
if len(imported) > 1:
    try:
        bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        print("Joined imported curves into single object:", obj.name)
    except RuntimeError as e:
        obj = imported[0]
        print("Join failed, using first imported object:", obj.name, e)
else:
    obj = imported[0]

# Set name
obj.name = "Engineering_Layout_Reference"
if hasattr(obj, "data") and obj.data is not None:
    try:
        obj.data.name = "Engineering_Layout_Reference"
    except Exception as e:
        print(f"Warning: failed to rename data-block for {obj.name}: {e}")

# Set origin to geometry and move to world origin
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
# Ensure cursor at world origin
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
# Move object to origin
obj.location = (0.0, 0.0, 0.0)

# Determine bounding size to compute camera distance
# Evaluate object dimensions (after transforms)
# object.dimensions returns bounding box size in object space times scale
dims = obj.dimensions
max_dim = max(dims.x, dims.y, dims.z)
if max_dim == 0:
    max_dim = 1.0
print("Object dimensions:", dims.x, dims.y, dims.z)

# Apply scale argument or auto-scale to fit camera view
if scale_arg:
    obj.scale = (scale_arg, scale_arg, scale_arg)
else:
    # Auto scale: make the object about 6 units wide
    target_width = 6.0
    uniform = target_width / max_dim
    obj.scale = (uniform, uniform, uniform)

# Optionally apply the scale to avoid later surprises
if apply_scale:
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Add a small text note near the object
note_text = "Imported from DXF via SVG — not to scale for fabrication"
# place text slightly below the object's bounding box
text_loc = Vector((0.0, 0.0, -0.1 * max_dim))

bpy.ops.object.text_add(location=(text_loc.x, text_loc.y, text_loc.z))
text_obj = bpy.context.active_object
text_obj.data.body = note_text
text_obj.name = "Import_Note"
# scale text down
text_obj.scale = (0.2, 0.2, 0.2)

# Create camera
cam_data = bpy.data.cameras.new("CAM")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)

# Position camera: place on +Y axis looking at origin
# distance based on object size
cam_distance = max_dim * 3.0
cam_obj.location = (0.0, -cam_distance, max_dim * 1.2)
# point camera at origin
direction = Vector((0.0, 0.0, 0.0)) - cam_obj.location
rot_quat = direction.to_track_quat("-Z", "Y")
cam_obj.rotation_euler = rot_quat.to_euler()

bpy.context.scene.camera = cam_obj

# Add light
light_data = bpy.data.lights.new(name="KeyLight", type="SUN")
light_obj = bpy.data.objects.new(name="KeyLight", object_data=light_data)
light_obj.location = (0.0, -cam_distance, max_dim * 2.0)
bpy.context.scene.collection.objects.link(light_obj)

# Adjust render settings
bpy.context.scene.render.engine = (
    "CYCLES" if "CYCLES" in bpy.context.scene.render.engine else "BLENDER_EEVEE"
)
bpy.context.scene.render.resolution_x = res_x
bpy.context.scene.render.resolution_y = res_y
bpy.context.scene.render.filepath = output_png
bpy.context.scene.render.image_settings.file_format = "PNG"

# Use a simple white background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 1, 1)
bg.inputs[1].default_value = 1.0

# Make the object visible and shade smooth if mesh
obj.select_set(True)

# Render
print("Rendering to", output_png)
try:
    bpy.ops.render.render(write_still=True)
    print("Render complete")
except RuntimeError as e:
    print("Render failed:", e)
    sys.exit(5)

sys.exit(0)
