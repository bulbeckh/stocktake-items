#!/bin/bash
for f in ../../*/meshes/*.glb; do
  echo $(realpath $f)
  blender -b --python render_glb.py -- "$(realpath $f)" "$(pwd)/$(basename "$f" .glb).png"
done
