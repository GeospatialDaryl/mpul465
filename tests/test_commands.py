from __future__ import annotations

import pytest

from mpul465.commands import CommandEncoder
from mpul465.constants import Alignment


def test_initialize() -> None:
    assert CommandEncoder().initialize() == b"\x1b@"


def test_line_feed() -> None:
    assert CommandEncoder().line_feed() == b"\x0a"


def test_feed_lines() -> None:
    assert CommandEncoder().feed_lines(3) == b"\x1bd\x03"


def test_feed_lines_zero() -> None:
    assert CommandEncoder().feed_lines(0) == b"\x1bd\x00"


def test_feed_lines_max() -> None:
    assert CommandEncoder().feed_lines(255) == b"\x1bd\xff"


def test_feed_lines_out_of_range() -> None:
    with pytest.raises(ValueError):
        CommandEncoder().feed_lines(256)


def test_bold_on() -> None:
    assert CommandEncoder().bold(True) == b"\x1bE\x01"


def test_bold_off() -> None:
    assert CommandEncoder().bold(False) == b"\x1bE\x00"


def test_underline_on() -> None:
    assert CommandEncoder().underline(True) == b"\x1b-\x01"


def test_underline_off() -> None:
    assert CommandEncoder().underline(False) == b"\x1b-\x00"


def test_align_left() -> None:
    assert CommandEncoder().align(Alignment.LEFT) == b"\x1ba\x00"


def test_align_center() -> None:
    assert CommandEncoder().align(Alignment.CENTER) == b"\x1ba\x01"


def test_align_right() -> None:
    assert CommandEncoder().align(Alignment.RIGHT) == b"\x1ba\x02"


def test_text_bytes_passthrough() -> None:
    data = b"Hello\n"
    assert CommandEncoder().text_bytes(data) == data


# ---------------------------------------------------------------------------
# Raster image — GS v 0 golden bytes
# ---------------------------------------------------------------------------

def test_raster_image_header_format() -> None:
    from mpul465.models import MonoRaster
    # 8×1 pixel image: stride=1, height=1, one byte of data (all black)
    raster = MonoRaster(width=8, height=1, data=b"\xff", stride=1)
    result = CommandEncoder().raster_image(raster)
    # GS v 0 m xL xH yL yH [data]
    assert result == b"\x1dv0\x00\x01\x00\x01\x00\xff"


def test_raster_image_two_byte_stride() -> None:
    from mpul465.models import MonoRaster
    # 16-wide image: stride=2, height=2
    data = b"\xaa\x55" * 2  # 4 bytes
    raster = MonoRaster(width=16, height=2, data=data, stride=2)
    result = CommandEncoder().raster_image(raster)
    assert result[:3] == b"\x1dv0"
    assert result[3] == 0           # m = normal density
    assert result[4] == 2           # xL = 2 (stride)
    assert result[5] == 0           # xH = 0
    assert result[6] == 2           # yL = 2 (height)
    assert result[7] == 0           # yH = 0
    assert result[8:] == data


def test_raster_image_data_appended_after_header() -> None:
    from mpul465.models import MonoRaster
    payload = bytes(range(48))  # 48 bytes, 8 rows of 48-bit stride
    raster = MonoRaster(width=48, height=8, data=payload, stride=6)
    result = CommandEncoder().raster_image(raster)
    assert result.endswith(payload)
    assert len(result) == 8 + len(payload)  # 8-byte header


# ---------------------------------------------------------------------------
# Barcode / QR — stubs must raise
# ---------------------------------------------------------------------------

def test_qr_returns_bytes() -> None:
    result = CommandEncoder().qr("https://example.com")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_barcode_returns_bytes() -> None:
    from mpul465.constants import BarcodeKind
    result = CommandEncoder().barcode("123456", BarcodeKind.CODE128)
    assert isinstance(result, bytes)
    assert len(result) > 0
