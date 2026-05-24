from __future__ import annotations

import pytest

from mpul465.exceptions import UnsupportedCharacterError
from mpul465.models import NativeTextSegment, RasterTextSegment
from tests.conftest import make_engine


def test_ascii_prints_native() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("Hello\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert segments[0].data == b"Hello\n"


def test_lambda_renders_raster_in_auto_mode() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("λ\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], RasterTextSegment)


def test_strict_mode_rejects_unsupported_char() -> None:
    engine = make_engine("cp437")
    with pytest.raises(UnsupportedCharacterError) as exc_info:
        engine.render_text("λ\n", fallback="strict")
    assert "λ" in exc_info.value.characters


def test_raster_mode_always_rasterizes_ascii() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("Hello\n", fallback="raster")
    assert all(isinstance(s, RasterTextSegment) for s in segments)


def test_ascii_only_line_stays_native_in_auto() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("ABC\n", fallback="auto")
    assert isinstance(segments[0], NativeTextSegment)


def test_unsupported_char_error_carries_character_set() -> None:
    engine = make_engine("cp437")
    with pytest.raises(UnsupportedCharacterError) as exc_info:
        engine.render_text("λ ⚙\n", fallback="strict")
    assert "λ" in exc_info.value.characters or "⚙" in exc_info.value.characters
