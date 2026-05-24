from __future__ import annotations

import math

from PIL import Image

from mpul465.graphics.packing import BitPacker


def test_stride_for_384_width() -> None:
    img = Image.new("1", (384, 1), 255)
    raster = BitPacker().pack_msb_first(img)
    assert raster.stride == 48  # ceil(384/8)


def test_data_length() -> None:
    img = Image.new("1", (384, 10), 255)
    raster = BitPacker().pack_msb_first(img)
    assert len(raster.data) == 48 * 10


def test_all_white_is_zero_bytes() -> None:
    img = Image.new("1", (8, 1), 255)  # white
    raster = BitPacker().pack_msb_first(img)
    assert raster.data == bytes([0x00])


def test_all_black_is_ff_bytes() -> None:
    img = Image.new("1", (8, 1), 0)  # black
    raster = BitPacker().pack_msb_first(img)
    assert raster.data == bytes([0xFF])


def test_leftmost_pixel_is_high_bit() -> None:
    img = Image.new("1", (8, 1), 255)
    img.putpixel((0, 0), 0)  # leftmost black
    raster = BitPacker().pack_msb_first(img)
    assert raster.data[0] == 0b10000000


def test_rightmost_pixel_is_low_bit() -> None:
    img = Image.new("1", (8, 1), 255)
    img.putpixel((7, 0), 0)  # rightmost black
    raster = BitPacker().pack_msb_first(img)
    assert raster.data[0] == 0b00000001


def test_inverted_polarity() -> None:
    img = Image.new("1", (8, 1), 0)  # all black
    raster = BitPacker().pack_msb_first(img, black_bit=0)
    assert raster.data == bytes([0x00])


def test_non_multiple_of_8_width() -> None:
    img = Image.new("1", (10, 1), 0)
    raster = BitPacker().pack_msb_first(img)
    assert raster.stride == math.ceil(10 / 8)  # 2
    assert len(raster.data) == 2
