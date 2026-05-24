from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.exceptions import ImageTooWideError
from mpul465.graphics import GraphicsEngine
from mpul465.graphics.packing import BitPacker
from mpul465.graphics.raster import Rasterizer
from mpul465.commands import CommandEncoder
from mpul465.transports.dry_run import DryRunTransport


def make_engine(dots: int = 384) -> GraphicsEngine:
    config = MPUL465Config(dots_per_line=dots)
    return GraphicsEngine(Rasterizer(), CommandEncoder(), config)


def test_fit_width_scales_to_dots_per_line() -> None:
    engine = make_engine(dots=384)
    img = Image.new("RGB", (800, 200), "white")
    result = engine.image_to_commands(img, width="fit")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_explicit_width_is_respected() -> None:
    engine = make_engine(dots=384)
    img = Image.new("RGB", (800, 200), "white")
    result = engine.image_to_commands(img, width=200)
    assert len(result) > 0


def test_image_too_wide_raises_without_fit() -> None:
    engine = make_engine(dots=100)
    img = Image.new("RGB", (200, 50), "white")
    with pytest.raises(ImageTooWideError) as exc_info:
        engine.image_to_commands(img, width=None)
    assert exc_info.value.image_width == 200
    assert exc_info.value.print_width == 100


def test_image_file_roundtrip(tmp_path: Path) -> None:
    img = Image.new("RGB", (100, 50), "white")
    img_path = tmp_path / "test.png"
    img.save(img_path)

    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.image(img_path, width="fit")

    assert len(transport.buffer) > 0


def test_grayscale_input_handled() -> None:
    engine = make_engine()
    img = Image.new("L", (384, 10), 128)
    result = engine.image_to_commands(img, width="fit")
    assert len(result) > 0


def test_rgba_input_handled() -> None:
    engine = make_engine()
    img = Image.new("RGBA", (384, 10), (0, 0, 0, 255))
    result = engine.image_to_commands(img, width="fit")
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Band streaming
# ---------------------------------------------------------------------------

def test_tall_image_produces_multiple_gs_v0_commands() -> None:
    # image_chunk_height=24 (default); 48-row image → 2 bands
    engine = make_engine(dots=32)
    img = Image.new("1", (32, 48), 0)
    result = engine.image_to_commands(img, width="fit")
    gs_v0 = b"\x1dv0"
    assert result.count(gs_v0) == 2


def test_image_chunk_height_controls_band_count() -> None:
    cfg = MPUL465Config(dots_per_line=32, image_chunk_height=10)
    engine = GraphicsEngine(Rasterizer(), CommandEncoder(), cfg)
    img = Image.new("1", (32, 31), 0)  # 31 rows / 10 = 4 bands (10,10,10,1)
    result = engine.image_to_commands(img, width="fit")
    assert result.count(b"\x1dv0") == 4


def test_single_band_image_produces_one_gs_v0() -> None:
    engine = make_engine(dots=64)
    img = Image.new("1", (64, 5), 0)  # 5 rows < 24 chunk height → 1 band
    result = engine.image_to_commands(img, width="fit")
    assert result.count(b"\x1dv0") == 1


# ---------------------------------------------------------------------------
# _resolve_width edge cases
# ---------------------------------------------------------------------------

def test_resolve_width_invalid_string_raises() -> None:
    engine = make_engine(dots=384)
    img = Image.new("RGB", (100, 10), "white")
    with pytest.raises(ValueError, match="Invalid width"):
        engine.image_to_commands(img, width="stretch")  # type: ignore[arg-type]


def test_resolve_width_natural_equals_dots_per_line_is_accepted() -> None:
    engine = make_engine(dots=100)
    img = Image.new("1", (100, 10), 0)
    result = engine.image_to_commands(img, width=None)
    assert len(result) > 0
