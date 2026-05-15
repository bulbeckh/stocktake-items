import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
input_path, output_path = argv

bpy.ops.object.delete()
bpy.ops.import_scene.gltf(filepath=input_path)

# Find model bounds
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
center = sum((o.location for o in objs), Vector()) / len(objs)

# Add camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam.location = center + Vector((2.5, -3.0, 2.0))
cam.rotation_euler = (math.radians(60), 0, math.radians(38))
bpy.context.scene.camera = cam

# Add light
light_data = bpy.data.lights.new("Key Light", "AREA")
light = bpy.data.objects.new("Key Light", light_data)
bpy.context.collection.objects.link(light)
light.location = center + Vector((2, -3, 4))
light_data.energy = 500
light_data.size = 5

# Render settings
scene = bpy.context.scene
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = output_path

bpy.ops.render.render(write_still=True)
