#!/usr/bin/env python3

"""
batch_replace_glb_images.py

Given one template GLB and multiple replacement PNG images, create one new GLB
per image.

The script preserves:
- mesh geometry
- UV mapping
- materials
- texture references
- scene hierarchy

It only replaces the embedded image payload used by a selected glTF image slot.
"""

from pathlib import Path
import argparse
from io import BytesIO

from PIL import Image as PILImage
from pygltflib import GLTF2, BufferView


def pad4(data: bytes) -> bytes:
    return data + (b"\x00" * ((-len(data)) % 4))


def image_dimensions_from_file(path: Path) -> tuple[int, int]:
    with PILImage.open(path) as img:
        return img.size


def image_dimensions_from_bytes(data: bytes) -> tuple[int, int]:
    with PILImage.open(BytesIO(data)) as img:
        return img.size


def replace_embedded_image(
    template_glb: Path,
    replacement_png: Path,
    output_glb: Path,
    image_index: int = 0,
    require_same_dimensions: bool = True,
) -> None:
    gltf = GLTF2().load(str(template_glb))

    if not gltf.images:
        raise ValueError(f"{template_glb} contains no images")

    if image_index >= len(gltf.images):
        raise IndexError(
            f"image_index {image_index} out of range; "
            f"GLB has {len(gltf.images)} image(s)"
        )

    target_image = gltf.images[image_index]

    if target_image.bufferView is None:
        raise ValueError(
            "Selected image is not embedded in the GLB. "
            "This script expects image.bufferView to be set."
        )

    old_blob = gltf.binary_blob()
    old_view = gltf.bufferViews[target_image.bufferView]

    old_image_bytes = old_blob[
        old_view.byteOffset : old_view.byteOffset + old_view.byteLength
    ]

    if require_same_dimensions:
        old_dims = image_dimensions_from_bytes(old_image_bytes)
        new_dims = image_dimensions_from_file(replacement_png)

        if old_dims != new_dims:
            raise ValueError(
                f"{replacement_png.name}: dimensions {new_dims} do not match "
                f"template image dimensions {old_dims}"
            )

    with open(replacement_png, "rb") as f:
        new_image_bytes = f.read()

    binary_blob = gltf.binary_blob() or b""

    # Append new PNG bytes to the binary chunk.
    aligned_blob = pad4(binary_blob)
    new_offset = len(aligned_blob)
    new_length = len(new_image_bytes)
    new_blob = pad4(aligned_blob + new_image_bytes)

    # Create a new bufferView for the replacement image.
    new_buffer_view = BufferView(
        buffer=0,
        byteOffset=new_offset,
        byteLength=new_length,
    )

    gltf.bufferViews.append(new_buffer_view)
    new_buffer_view_index = len(gltf.bufferViews) - 1

    # Repoint the existing image object to the new PNG.
    target_image.bufferView = new_buffer_view_index
    target_image.mimeType = "image/png"
    target_image.uri = None

    gltf.buffers[0].byteLength = len(new_blob)
    gltf.set_binary_blob(new_blob)

    output_glb.parent.mkdir(parents=True, exist_ok=True)
    gltf.save(str(output_glb))


def safe_stem(path: Path) -> str:
    return path.stem.replace(" ", "_")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create multiple GLB models from one template GLB and many PNG textures."
    )

    parser.add_argument(
        "template_glb",
        type=Path,
        help="Input/template GLB containing the original embedded texture.",
    )

    parser.add_argument(
        "png_images",
        type=Path,
        nargs="+",
        help="Replacement PNG images. One output GLB is created per image.",
    )

    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("generated_models"),
        help="Directory where output GLBs will be written.",
    )

    parser.add_argument(
        "--prefix",
        default=None,
        help="Optional output filename prefix. Defaults to template GLB stem.",
    )

    parser.add_argument(
        "--image-index",
        type=int,
        default=0,
        help="Index of the glTF image slot to replace. Default: 0.",
    )

    parser.add_argument(
        "--allow-different-dimensions",
        action="store_true",
        help="Allow replacement PNGs to have different dimensions from the original.",
    )

    args = parser.parse_args()

    prefix = args.prefix or args.template_glb.stem

    for png in args.png_images:
        if png.suffix.lower() != ".png":
            raise ValueError(f"{png} is not a PNG file")

        output_glb = args.out_dir / f"{safe_stem(png)}.glb"

        replace_embedded_image(
            template_glb=args.template_glb,
            replacement_png=png,
            output_glb=output_glb,
            image_index=args.image_index,
            require_same_dimensions=not args.allow_different_dimensions,
        )

        print(f"Created: {output_glb}")


if __name__ == "__main__":
    main()
