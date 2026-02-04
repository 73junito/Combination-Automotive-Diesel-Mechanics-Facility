"""
Blender script to import an SVG, center and scale it, set an orthographic top-down camera,
and render a high-resolution PNG.

Run inside Blender:
blender --background --python blender_render_svg.py -- <input_svg> <output_png> <res_x> <res_y>

Example:
blender --background --python blender_render_svg.py -- "C:\path\to\facility_layout.svg" "C:\path\to\facility_layout_render.png" 3840 2160

Notes:
- Run this with Blender (bpy is available only inside Blender's Python).
- The script converts imported curves to meshes, assigns an emission material for crisp rendering,
  positions an orthographic camera to fit the drawing, sets white background, and renders.
"""

import os
import sys

# This script must be run in Blender's bundled Python (bpy available)
try:
    import math

    import bpy
    import mathutils
    from mathutils import Vector
except ImportError as e:
    print("This script requires Blender (run with blender --background --python)")
    raise

# Parse args after '--'
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1 :]
else:
    argv = []

if len(argv) < 2:
    print(
        "Usage: blender --background --python blender_render_svg.py -- <input_svg> <output_png> [res_x res_y]"
    )
    sys.exit(2)

input_svg = os.path.abspath(argv[0])
output_png = os.path.abspath(argv[1])
res_x = int(argv[2]) if len(argv) > 2 else 3840
res_y = int(argv[3]) if len(argv) > 3 else 2160

print("Input SVG:", input_svg)
print("Output PNG:", output_png)
print("Resolution:", res_x, "x", res_y)

# Clear existing objects
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Import SVG
if not os.path.exists(input_svg):
    print("SVG not found:", input_svg)
    sys.exit(2)

bpy.ops.import_curve.svg(filepath=input_svg)

# Collect imported objects
imported = [
    o
    for o in bpy.context.scene.objects
    if o.select_get() or o.type in {"CURVE", "MESH"}
]
if not imported:
    # fallback: take all objects
    imported = list(bpy.context.scene.objects)

# If nothing imported, exit
if not imported:
    print("No objects found after import.")
    sys.exit(2)

# Convert curves to mesh and join into a single object
meshes = []
for obj in imported:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "CURVE":
        try:
            bpy.ops.object.convert(target="MESH")
        except RuntimeError:
            pass
    if obj.type == "MESH":
        meshes.append(obj)
    obj.select_set(False)

# Re-collect meshes
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    print("No mesh objects to render.")
    sys.exit(2)

# Join meshes into single object for easy bounding box
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
try:
    bpy.ops.object.join()
except RuntimeError:
    pass

main_obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
main_obj.name = "Imported_Drawing"

# Create a simple emission material for crisp lines/fills
mat = bpy.data.materials.get("svg_emission")
if mat is None:
    mat = bpy.data.materials.new("svg_emission")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)  # black
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

if main_obj.data.materials:
    main_obj.data.materials[0] = mat
else:
    main_obj.data.materials.append(mat)

# Set object origin to geometry center
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

# Compute bounding box in world coords
bbox_corners = [main_obj.matrix_world @ Vector(corner) for corner in main_obj.bound_box]
min_corner = Vector(
    (
        min([v.x for v in bbox_corners]),
        min([v.y for v in bbox_corners]),
        min([v.z for v in bbox_corners]),
    )
)
max_corner = Vector(
    (
        max([v.x for v in bbox_corners]),
        max([v.y for v in bbox_corners]),
        max([v.z for v in bbox_corners]),
    )
)
center = (min_corner + max_corner) / 2.0
width = max_corner.x - min_corner.x
height = max_corner.y - min_corner.y
print("Bounding box center:", center)
print("Width x Height:", width, "x", height)

# Create camera
cam_data = bpy.data.cameras.new("SVG_Cam")
cam = bpy.data.objects.new("SVG_Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam_data.type = "ORTHO"
# Set ortho scale to fit object (add margin)
margin = 0.05
max_dim = max(width, height)
if max_dim == 0:
    max_dim = 10.0
cam_data.ortho_scale = max_dim * (1.0 + margin)

# Position camera above center
cam.location = (center.x, center.y, center.z + max_dim * 2.0)
# Point camera downwards
cam.rotation_euler = (0.0, 0.0, 0.0)
cam.rotation_euler[0] = 0.0
# rotate to top-down: point -Z
cam.rotation_mode = "XYZ"
cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)

# Create an empty light (not needed for emission materials) but ensure world background
bpy.context.scene.world.use_nodes = True
world_nodes = bpy.context.scene.world.node_tree.nodes
bg = world_nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

# Set render settings
scene = bpy.context.scene
scene.camera = cam
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = output_png
scene.render.resolution_x = res_x
scene.render.resolution_y = res_y
scene.render.resolution_percentage = 100

# Optional: set transparent background? We'll keep white
# Render
print("Rendering...")
bpy.ops.render.render(write_still=True)
print("Saved:", output_png)

# Done
