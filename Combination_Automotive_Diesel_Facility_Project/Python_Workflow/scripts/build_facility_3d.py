import bpy

# ---------- Cleanup ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# ---------- Units / scale ----------
SCALE = 0.05  # convert SVG-ish units to meters


def add_box(name, x, y, z, sx, sy, sz, mat=None):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (sx, sy, sz)
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    return obj


# ---------- Materials ----------
def make_mat(name, color):
    mat = bpy.data.materials.new(name=name)
    # Use Principled BSDF if available
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    else:
        mat.diffuse_color = (*color, 1.0)
    return mat


mat_concrete = make_mat("Concrete", (0.8, 0.8, 0.82))
mat_metal = make_mat("Metal", (0.5, 0.55, 0.6))
mat_glass = make_mat("Glass", (0.5, 0.7, 0.9))
mat_asphalt = make_mat("Asphalt", (0.15, 0.15, 0.18))
mat_green = make_mat("Landscape", (0.3, 0.6, 0.3))

# ---------- Building shell ----------
bld_w = 2080 * SCALE
bld_d = 1180 * SCALE
bld_h = 8.0

building = add_box(
    "Building",
    x=0.0,
    y=0.0,
    z=bld_h / 2,
    sx=bld_w / 2,
    sy=bld_d / 2,
    sz=bld_h / 2,
    mat=mat_concrete,
)

# ---------- Roof band ----------
roof = add_box(
    "RoofBand",
    x=0.0,
    y=0.0,
    z=bld_h + 0.3,
    sx=bld_w / 2,
    sy=bld_d / 2,
    sz=0.3,
    mat=mat_metal,
)

# ---------- Service bays ----------
num_bays = 16
bay_w_svg = 90
bay_gap_svg = 10
bay_d_svg = 230
bay_h = 5.0

total_bays_width_svg = num_bays * bay_w_svg + (num_bays - 1) * bay_gap_svg
total_bays_width = total_bays_width_svg * SCALE

start_x = -total_bays_width / 2 + (bay_w_svg * SCALE) / 2
front_y = bld_d / 2 - (bay_d_svg * SCALE) / 2

for i in range(num_bays):
    x = start_x + i * (bay_w_svg + bay_gap_svg) * SCALE
    add_box(
        f"Bay_{i+1}",
        x=x,
        y=front_y,
        z=bay_h / 2,
        sx=(bay_w_svg * SCALE) / 2,
        sy=(bay_d_svg * SCALE) / 2,
        sz=bay_h / 2,
        mat=mat_concrete,
    )

# ---------- Customer / office block ----------
cust_w_svg = 600
cust_d_svg = 280
cust_h = 4.0

cust_x = -bld_w / 2 + (cust_w_svg * SCALE) / 2 + 0.5
cust_y = -bld_d / 2 + (cust_d_svg * SCALE) / 2 + 0.5

add_box(
    "CustomerOffice",
    x=cust_x,
    y=cust_y,
    z=cust_h / 2,
    sx=(cust_w_svg * SCALE) / 2,
    sy=(cust_d_svg * SCALE) / 2,
    sz=cust_h / 2,
    mat=mat_concrete,
)

# ---------- Glass entrance ----------
entr_w_svg = 260
entr_h = 3.0
entr_d = 1.0

entr_x = cust_x
entr_y = bld_d / 2 + entr_d / 2
entr_z = entr_h / 2

add_box(
    "EntranceGlass",
    x=entr_x,
    y=entr_y,
    z=entr_z,
    sx=(entr_w_svg * SCALE) / 2,
    sy=entr_d / 2,
    sz=entr_h / 2,
    mat=mat_glass,
)

# ---------- Service drive ----------
drive_depth = 10.0
add_box(
    "ServiceDrive",
    x=0.0,
    y=bld_d / 2 + drive_depth / 2,
    z=0.01,
    sx=bld_w / 2,
    sy=drive_depth / 2,
    sz=0.01,
    mat=mat_asphalt,
)

# ---------- Parking ----------
slot_w = 2.7
slot_d = 5.5
num_slots = 10
start_px = -(num_slots * slot_w) / 2 + slot_w / 2
park_y = -bld_d / 2 - slot_d / 2 - 2.0

for i in range(num_slots):
    px = start_px + i * slot_w
    add_box(
        f"Parking_{i+1}",
        x=px,
        y=park_y,
        z=0.02,
        sx=slot_w / 2,
        sy=slot_d / 2,
        sz=0.02,
        mat=mat_asphalt,
    )

# ---------- Landscaping ----------
add_box(
    "LandscapeStrip",
    x=bld_w / 2 + 2.0,
    y=0.0,
    z=0.1,
    sx=1.0,
    sy=bld_d / 2,
    sz=0.1,
    mat=mat_green,
)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (bld_w, -bld_d, bld_h * 1.5)
cam_obj.rotation_euler = (1.0, 0.0, 0.8)
bpy.context.scene.camera = cam_obj

# ---------- Sun light ----------
light_data = bpy.data.lights.new(name="Sun", type="SUN")
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (bld_w, bld_d, bld_h * 2)

print("3D facility created.")
