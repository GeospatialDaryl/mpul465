from __future__ import annotations

from PIL import Image


def apply_dither(image: Image.Image, mode: str) -> Image.Image:
    """Convert a grayscale image to 1-bit using the specified dither mode."""
    if image.mode != "L":
        image = image.convert("L")
    dither = Image.Dither.FLOYDSTEINBERG if mode == "floyd-steinberg" else Image.Dither.NONE
    return image.convert("1", dither=dither)
