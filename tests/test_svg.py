from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.commands import CommandEncoder
from mpul465.exceptions import SVGRenderError
from mpul465.graphics import GraphicsEngine
from mpul465.graphics.raster import Rasterizer
from mpul465.graphics.vector import VectorRenderer
from mpul465.transports.dry_run import DryRunTransport

# ---------------------------------------------------------------------------
# Minimal test SVG — 16×16 black rectangle
# ---------------------------------------------------------------------------

_SIMPLE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
    b'<rect width="16" height="16" fill="black"/>'
    b"</svg>"
)

_SMALL_SVG_STR = _SIMPLE_SVG.decode()

# ---------------------------------------------------------------------------
# VectorRenderer — import guard
# ---------------------------------------------------------------------------


def test_vector_renderer_raises_svg_error_when_cairosvg_missing() -> None:
    renderer = VectorRenderer()
    with patch.dict(sys.modules, {"cairosvg": None}):
        with pytest.raises(SVGRenderError, match="mpul465\\[svg\\]"):
            renderer.render(_SIMPLE_SVG)


# ---------------------------------------------------------------------------
# VectorRenderer — successful renders
# ---------------------------------------------------------------------------


def test_vector_renderer_returns_png_bytes_from_bytes_input() -> None:
    renderer = VectorRenderer()
    result = renderer.render(_SIMPLE_SVG)
    assert isinstance(result, bytes)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic


def test_vector_renderer_accepts_str_path() -> None:
    renderer = VectorRenderer()
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(_SIMPLE_SVG)
        tmp_path = f.name
    result = renderer.render(tmp_path)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"


def test_vector_renderer_accepts_path_object() -> None:
    renderer = VectorRenderer()
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(_SIMPLE_SVG)
        tmp_path = Path(f.name)
    result = renderer.render(tmp_path)
    assert result[:8] == b"\x89PNG\r\n\x1a\n"


def test_vector_renderer_output_width_is_respected() -> None:
    renderer = VectorRenderer()
    result = renderer.render(_SIMPLE_SVG, output_width=64)
    img = Image.open(io.BytesIO(result))
    assert img.width == 64


def test_vector_renderer_bad_svg_raises_svg_render_error() -> None:
    renderer = VectorRenderer()
    with pytest.raises(SVGRenderError, match="CairoSVG"):
        renderer.render(b"not valid xml at all <<<")


# ---------------------------------------------------------------------------
# GraphicsEngine.svg_to_commands — full pipeline
# ---------------------------------------------------------------------------


def _make_engine(dots: int = 64) -> GraphicsEngine:
    cfg = MPUL465Config(dots_per_line=dots)
    return GraphicsEngine(Rasterizer(), CommandEncoder(), cfg)


def test_svg_to_commands_returns_nonempty_bytes() -> None:
    engine = _make_engine()
    result = engine.svg_to_commands(_SIMPLE_SVG)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_svg_to_commands_width_fit_uses_dots_per_line() -> None:
    engine = _make_engine(dots=64)
    result_fit = engine.svg_to_commands(_SIMPLE_SVG, width="fit")
    result_explicit = engine.svg_to_commands(_SIMPLE_SVG, width=64)
    # Both should produce the same byte stream — same raster width
    assert result_fit == result_explicit


def test_svg_to_commands_explicit_width() -> None:
    engine = _make_engine(dots=384)
    result = engine.svg_to_commands(_SIMPLE_SVG, width=32)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_svg_to_commands_contains_gs_v_0_command() -> None:
    engine = _make_engine(dots=64)
    result = engine.svg_to_commands(_SIMPLE_SVG)
    # GS v 0 is b"\x1dv0" — the raster image command prefix
    assert b"\x1dv0" in result


def test_svg_to_commands_missing_cairosvg_raises_svg_render_error() -> None:
    engine = _make_engine()
    fake_renderer = VectorRenderer.__new__(VectorRenderer)

    def _raise(svg: object, *, output_width: object = None) -> bytes:
        raise SVGRenderError("CairoSVG not installed")

    fake_renderer.render = _raise  # type: ignore[method-assign]
    engine._vector = fake_renderer
    with pytest.raises(SVGRenderError):
        engine.svg_to_commands(_SIMPLE_SVG)


def test_svg_to_commands_str_path_input() -> None:
    engine = _make_engine()
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(_SIMPLE_SVG)
        tmp = f.name
    result = engine.svg_to_commands(tmp)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# MPUL465Printer.svg — facade integration
# ---------------------------------------------------------------------------


def test_printer_svg_method_produces_output() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.svg(_SIMPLE_SVG)
    assert len(transport.buffer) > 0
    assert b"\x1dv0" in transport.buffer


def test_printer_svg_width_fit() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.svg(_SIMPLE_SVG, width="fit")
    assert len(transport.buffer) > 0


def test_printer_svg_explicit_width() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(dots_per_line=384)
    with MPUL465Printer(transport, cfg) as printer:
        printer.svg(_SIMPLE_SVG, width=32)
    assert len(transport.buffer) > 0
