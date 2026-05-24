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
