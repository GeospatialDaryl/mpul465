from __future__ import annotations

import pytest

from mpul465 import MPUL465Config
from mpul465.exceptions import UnsupportedCharacterError
from mpul465.models import NativeTextSegment, RasterTextSegment
from mpul465.text.codepages import UnicodePolicy
from mpul465.text.wrapping import NativeFontMetrics
from tests.conftest import make_engine


# ---------------------------------------------------------------------------
# Basic fallback modes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# NATIVE fallback mode — replacement character
# ---------------------------------------------------------------------------

def test_native_mode_replaces_unsupported_with_question_mark() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("λ\n", fallback="native")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert b"?" in segments[0].data


def test_native_mode_uses_custom_replacement() -> None:
    from mpul465.text.codepages import CodePage
    from mpul465.text.engine import TextEngine, TextRasterizer
    from mpul465.text.fonts import FontRegistry

    cfg = MPUL465Config(native_codepage="cp437")
    policy = UnicodePolicy(replacement="*")
    engine = TextEngine(
        CodePage("cp437"),
        TextRasterizer(FontRegistry(), cfg),
        cfg,
        unicode_policy=policy,
    )
    segments = engine.render_text("λ\n", fallback="native")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"*" in segments[0].data


# ---------------------------------------------------------------------------
# Unicode normalization
# ---------------------------------------------------------------------------

def test_nfc_normalization_allows_native_encoding() -> None:
    from mpul465.text.codepages import CodePage
    from mpul465.text.engine import TextEngine, TextRasterizer
    from mpul465.text.fonts import FontRegistry

    cfg = MPUL465Config(native_codepage="cp437")
    policy = UnicodePolicy(normalize="NFC")
    engine = TextEngine(
        CodePage("cp437"),
        TextRasterizer(FontRegistry(), cfg),
        cfg,
        unicode_policy=policy,
    )
    # Decomposed: e + U+0301 combining acute → NFC gives é, encodable in cp437
    decomposed = "é"
    segments = engine.render_text(decomposed + "\n", fallback="auto")
    assert isinstance(segments[0], NativeTextSegment)


def test_transliterate_makes_accented_text_native() -> None:
    from mpul465.text.codepages import CodePage
    from mpul465.text.engine import TextEngine, TextRasterizer
    from mpul465.text.fonts import FontRegistry

    cfg = MPUL465Config(native_codepage="ascii")
    policy = UnicodePolicy(transliterate=True)
    engine = TextEngine(
        CodePage("ascii"),
        TextRasterizer(FontRegistry(), cfg),
        cfg,
        unicode_policy=policy,
    )
    # "café" → "cafe" after transliteration → encodable as ASCII
    segments = engine.render_text("café\n", fallback="strict")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"cafe" in segments[0].data


# ---------------------------------------------------------------------------
# Wrapping — raster
# ---------------------------------------------------------------------------

def test_wrap_false_does_not_split_long_line() -> None:
    engine = make_engine("cp437")
    long_line = "A" * 200 + "\n"
    segments = engine.render_text(long_line, wrap=False)
    assert len(segments) == 1


def test_wrap_raster_splits_long_line() -> None:
    engine = make_engine("cp437")
    long_line = "λ " * 30 + "\n"
    segments = engine.render_text(long_line, fallback="raster", wrap=True)
    assert len(segments) > 1
    assert all(isinstance(s, RasterTextSegment) for s in segments)


def test_wrap_auto_uses_raster_for_unsupported() -> None:
    engine = make_engine("cp437")
    long_line = "λ " * 30 + "\n"
    segments = engine.render_text(long_line, fallback="auto", wrap=True)
    assert all(isinstance(s, RasterTextSegment) for s in segments)


# ---------------------------------------------------------------------------
# Wrapping — native
# ---------------------------------------------------------------------------

def test_wrap_native_splits_by_column_count() -> None:
    from mpul465.text.codepages import CodePage
    from mpul465.text.engine import TextEngine, TextRasterizer
    from mpul465.text.fonts import FontRegistry

    cfg = MPUL465Config(native_codepage="cp437")
    metrics = NativeFontMetrics(columns_normal=10, columns_double_width=5)
    engine = TextEngine(
        CodePage("cp437"),
        TextRasterizer(FontRegistry(), cfg),
        cfg,
        native_font_metrics=metrics,
    )
    # 25 chars → wraps into 3 lines of ≤10 chars
    segments = engine.render_text("A" * 25 + "\n", wrap=True)
    assert len(segments) == 3
    assert all(isinstance(s, NativeTextSegment) for s in segments)


def test_wrap_native_without_metrics_passthrough() -> None:
    engine = make_engine("cp437")
    line = "A" * 200 + "\n"
    segments = engine.render_text(line, wrap=True)
    # No NativeFontMetrics → passes through unchanged
    assert len(segments) == 1
