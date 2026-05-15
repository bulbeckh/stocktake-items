import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
input_path, output_path = argv

bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=input_path)

# Find model bounds
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not objs:
    raise RuntimeError(f"No mesh objects found in {input_path}")

bounds = [obj.matrix_world @ Vector(corner) for obj in objs for corner in obj.bound_box]
min_corner = Vector((min(v.x for v in bounds), min(v.y for v in bounds), min(v.z for v in bounds)))
max_corner = Vector((max(v.x for v in bounds), max(v.y for v in bounds), max(v.z for v in bounds)))
center = (min_corner + max_corner) / 2

# Add camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

view_direction = Vector((2.5, -3.0, 2.0)).normalized()
cam.rotation_euler = (-view_direction).to_track_quat("-Z", "Y").to_euler()
cam_data.lens = 70

scene = bpy.context.scene
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

# Fit the whole model in frame. Lower padding means a tighter crop.
padding = 1.15
tan_x = math.tan(cam_data.angle_x / 2)
tan_y = math.tan(cam_data.angle_y / 2)
rot_inv = cam.rotation_euler.to_matrix().inverted()
distance = 0
for corner in bounds:
    local = rot_inv @ (corner - center)
    distance = max(
        distance,
        local.z + abs(local.x) / tan_x,
        local.z + abs(local.y) / tan_y,
    )

cam.location = center + view_direction * distance * padding
bpy.context.scene.camera = cam

# Add light
light_data = bpy.data.lights.new("Key Light", "AREA")
light = bpy.data.objects.new("Key Light", light_data)
bpy.context.collection.objects.link(light)
light.location = center + Vector((2, -3, 4)).normalized() * max(distance, 1)
light_data.energy = 500
light_data.size = 5

# Render settings
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = output_path

bpy.ops.render.render(write_still=True)
