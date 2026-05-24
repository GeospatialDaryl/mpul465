from __future__ import annotations

import math
from typing import Literal

from PIL import Image

from mpul465.models import MonoRaster


class BitPacker:
    """Packs a 1-bit Pillow image into a MonoRaster byte array."""

    def pack_msb_first(
        self,
        image: Image.Image,
        *,
        black_bit: Literal[0, 1] = 1,
        bit_order: Literal["msb", "lsb"] = "msb",
    ) -> MonoRaster:
        if image.mode != "1":
            image = image.convert("1", dither=Image.Dither.NONE)

        width, height = image.size
        stride = math.ceil(width / 8)
        buf = bytearray(stride * height)

        for y in range(height):
            for x in range(width):
                pixel = image.getpixel((x, y))
                is_black = pixel == 0  # PIL mode "1": 0=black, 255=white
                bit = black_bit if is_black else (1 - black_bit)
                if bit:
                    byte_idx = y * stride + x // 8
                    if bit_order == "msb":
                        buf[byte_idx] |= 1 << (7 - x % 8)
                    else:
                        buf[byte_idx] |= 1 << (x % 8)

        return MonoRaster(width=width, height=height, data=bytes(buf), stride=stride)
