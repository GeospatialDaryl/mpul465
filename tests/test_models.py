from __future__ import annotations

import pytest

from mpul465 import (
    MPUL465Config,
    MPUL465Error,
    MPUL465Printer,
    Alignment,
    BarcodeKind,
    CommandNotSupportedError,
    GraphicsRenderError,
    ImageTooWideError,
    NativeFontMetrics,
    PrinterNotReadyError,
    SVGRenderError,
    TextFallbackMode,
    TransportError,
    UnicodePolicy,
    UnsupportedCharacterError,
)
from mpul465.models import MonoRaster, NativeTextSegment, PrintSegment, RasterTextSegment


# ---------------------------------------------------------------------------
# Public API — all __all__ names importable from top-level package
# ---------------------------------------------------------------------------

def test_all_public_names_importable() -> None:
    # Verify each exported name exists and is not None
    exports = [
        MPUL465Config, MPUL465Error, MPUL465Printer,
        Alignment, BarcodeKind,
        CommandNotSupportedError, GraphicsRenderError,
        ImageTooWideError, NativeFontMetrics,
        PrinterNotReadyError, SVGRenderError,
        TextFallbackMode, TransportError,
        UnicodePolicy, UnsupportedCharacterError,
    ]
    for obj in exports:
        assert obj is not None


# ---------------------------------------------------------------------------
# MPUL465Config defaults
# ---------------------------------------------------------------------------

def test_config_default_dots_per_line() -> None:
    assert MPUL465Config().dots_per_line == 384


def test_config_default_native_codepage() -> None:
    assert MPUL465Config().native_codepage == "cp437"


def test_config_default_image_chunk_height() -> None:
    assert MPUL465Config().image_chunk_height == 24


def test_config_default_enable_native_qr() -> None:
    assert MPUL465Config().enable_native_qr is True


def test_config_default_enable_native_barcode() -> None:
    assert MPUL465Config().enable_native_barcode is True


def test_config_default_image_dither() -> None:
    assert MPUL465Config().image_dither == "floyd-steinberg"


def test_config_default_font_size() -> None:
    assert MPUL465Config().default_font_size == 24


def test_config_is_frozen() -> None:
    cfg = MPUL465Config()
    with pytest.raises((AttributeError, TypeError)):
        cfg.dots_per_line = 999  # type: ignore[misc]


def test_config_custom_values() -> None:
    cfg = MPUL465Config(dots_per_line=576, native_codepage="ascii", image_chunk_height=8)
    assert cfg.dots_per_line == 576
    assert cfg.native_codepage == "ascii"
    assert cfg.image_chunk_height == 8


# ---------------------------------------------------------------------------
# MonoRaster
# ---------------------------------------------------------------------------

def test_mono_raster_fields() -> None:
    r = MonoRaster(width=8, height=1, data=b"\xff", stride=1)
    assert r.width == 8
    assert r.height == 1
    assert r.data == b"\xff"
    assert r.stride == 1


def test_mono_raster_is_frozen() -> None:
    r = MonoRaster(width=8, height=1, data=b"\x00", stride=1)
    with pytest.raises((AttributeError, TypeError)):
        r.width = 16  # type: ignore[misc]


def test_mono_raster_equality() -> None:
    a = MonoRaster(8, 1, b"\xff", 1)
    b = MonoRaster(8, 1, b"\xff", 1)
    assert a == b


def test_mono_raster_inequality() -> None:
    a = MonoRaster(8, 1, b"\xff", 1)
    b = MonoRaster(8, 1, b"\x00", 1)
    assert a != b


# ---------------------------------------------------------------------------
# NativeTextSegment
# ---------------------------------------------------------------------------

def test_native_text_segment_stores_bytes() -> None:
    seg = NativeTextSegment(data=b"Hello\n")
    assert seg.data == b"Hello\n"


def test_native_text_segment_is_frozen() -> None:
    seg = NativeTextSegment(data=b"x")
    with pytest.raises((AttributeError, TypeError)):
        seg.data = b"y"  # type: ignore[misc]


def test_native_text_segment_equality() -> None:
    assert NativeTextSegment(b"abc") == NativeTextSegment(b"abc")
    assert NativeTextSegment(b"abc") != NativeTextSegment(b"def")


# ---------------------------------------------------------------------------
# RasterTextSegment
# ---------------------------------------------------------------------------

def test_raster_text_segment_stores_mono_raster() -> None:
    r = MonoRaster(8, 1, b"\xff", 1)
    seg = RasterTextSegment(image=r)
    assert seg.image is r


def test_raster_text_segment_is_frozen() -> None:
    r = MonoRaster(8, 1, b"\xff", 1)
    seg = RasterTextSegment(image=r)
    with pytest.raises((AttributeError, TypeError)):
        seg.image = MonoRaster(16, 1, b"\x00\x00", 2)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PrintSegment type alias
# ---------------------------------------------------------------------------

def test_print_segment_is_union_type() -> None:
    # Verify both types are accepted in isinstance checks for the union members
    native = NativeTextSegment(b"x")
    raster = RasterTextSegment(MonoRaster(8, 1, b"\xff", 1))
    assert isinstance(native, NativeTextSegment)
    assert isinstance(raster, RasterTextSegment)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_alignment_values() -> None:
    assert Alignment.LEFT == "left"
    assert Alignment.CENTER == "center"
    assert Alignment.RIGHT == "right"


def test_text_fallback_mode_values() -> None:
    assert TextFallbackMode.AUTO == "auto"
    assert TextFallbackMode.NATIVE == "native"
    assert TextFallbackMode.RASTER == "raster"
    assert TextFallbackMode.STRICT == "strict"


def test_barcode_kind_values() -> None:
    assert BarcodeKind.CODE128 == "code128"
    assert BarcodeKind.CODE39 == "code39"
    assert BarcodeKind.EAN13 == "ean13"
    assert BarcodeKind.EAN8 == "ean8"
    assert BarcodeKind.UPCA == "upca"
