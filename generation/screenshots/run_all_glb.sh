#!/bin/bash
for f in assets/models/*.glb; do
  blender -b --python render_glb.py -- "$f" "screenshots/$(basename "$f" .glb).png"
done
