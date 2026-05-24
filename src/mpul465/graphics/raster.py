from __future__ import annotations

from PIL import Image, ImageOps


class Rasterizer:
    """Loads and converts images to 1-bit Pillow Images ready for bit packing."""

    def prepare(
        self,
        image: Image.Image,
        *,
        target_width: int,
        dither: str = "floyd-steinberg",
    ) -> Image.Image:
        img = ImageOps.exif_transpose(image)
        img = img.convert("L")

        if img.width != target_width:
            ratio = target_width / img.width
            new_height = max(1, round(img.height * ratio))
            img = img.resize((target_width, new_height), Image.LANCZOS)

        dither_mode = (
            Image.Dither.FLOYDSTEINBERG
            if dither == "floyd-steinberg"
            else Image.Dither.NONE
        )
        return img.convert("1", dither=dither_mode)
