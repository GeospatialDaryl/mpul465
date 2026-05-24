from __future__ import annotations

import pytest

from mpul465 import MPUL465Config
from mpul465.exceptions import UnsupportedCharacterError
from mpul465.models import NativeTextSegment, RasterTextSegment
from mpul465.text.codepages import CodePage, UnicodePolicy
from mpul465.text.engine import TextEngine, TextRasterizer
from mpul465.text.fonts import FontRegistry
from mpul465.text.wrapping import NativeFontMetrics
from tests.conftest import make_engine


def _make_engine_with(
    codepage: str = "cp437",
    policy: UnicodePolicy | None = None,
    metrics: NativeFontMetrics | None = None,
) -> TextEngine:
    cfg = MPUL465Config(native_codepage=codepage)
    return TextEngine(
        CodePage(codepage),
        TextRasterizer(FontRegistry(), cfg),
        cfg,
        unicode_policy=policy,
        native_font_metrics=metrics,
    )


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
# Edge cases — normative table from docs/text-and-unicode.md
# ---------------------------------------------------------------------------

def test_empty_string_returns_no_segments() -> None:
    engine = make_engine("cp437")
    for mode in ("auto", "strict", "native", "raster"):
        assert engine.render_text("", fallback=mode) == [], f"failed for fallback={mode!r}"


def test_whitespace_only_is_native_in_auto() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("   \n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)


def test_whitespace_only_is_native_in_strict() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("   \n", fallback="strict")
    assert isinstance(segments[0], NativeTextSegment)


def test_whitespace_only_is_native_in_native_mode() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("   \n", fallback="native")
    assert isinstance(segments[0], NativeTextSegment)


def test_whitespace_only_is_raster_in_raster_mode() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("   \n", fallback="raster")
    assert len(segments) == 1
    assert isinstance(segments[0], RasterTextSegment)


def test_only_newline_is_native_in_auto() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert segments[0].data == b"\n"


def test_only_newline_is_raster_in_raster_mode() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("\n", fallback="raster")
    assert len(segments) == 1
    assert isinstance(segments[0], RasterTextSegment)


def test_multi_line_produces_one_segment_per_line_native() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("Line1\nLine2\nLine3\n", fallback="auto")
    assert len(segments) == 3
    assert all(isinstance(s, NativeTextSegment) for s in segments)


def test_multi_line_produces_one_segment_per_line_raster() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("A\nB\nC\n", fallback="raster")
    assert len(segments) == 3
    assert all(isinstance(s, RasterTextSegment) for s in segments)


def test_all_unsupported_rasterizes_in_auto() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("λΩπ\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], RasterTextSegment)


def test_all_unsupported_raises_in_strict() -> None:
    engine = make_engine("cp437")
    with pytest.raises(UnsupportedCharacterError):
        engine.render_text("λΩπ\n", fallback="strict")


def test_all_unsupported_replaced_in_native() -> None:
    engine = make_engine("cp437")
    # λ (U+03BB) is not in cp437; use three of them to get three replacements
    segments = engine.render_text("λλλ\n", fallback="native")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert segments[0].data == b"???\n"


def test_trailing_text_without_newline_still_rendered() -> None:
    # Input without trailing newline should still produce a segment
    engine = make_engine("cp437")
    segments = engine.render_text("Hello")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert b"Hello" in segments[0].data


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
    engine = _make_engine_with("cp437", policy=UnicodePolicy(replacement="*"))
    segments = engine.render_text("λ\n", fallback="native")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"*" in segments[0].data


def test_native_mode_preserves_encodable_chars_around_replacement() -> None:
    engine = make_engine("cp437")
    # "A λ B\n" → "A ? B\n" — surrounding ASCII preserved
    segments = engine.render_text("A λ B\n", fallback="native")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"A" in segments[0].data
    assert b"B" in segments[0].data
    assert b"?" in segments[0].data


# ---------------------------------------------------------------------------
# Unicode normalization
# ---------------------------------------------------------------------------

def test_nfc_normalization_allows_native_encoding() -> None:
    engine = _make_engine_with("cp437", policy=UnicodePolicy(normalize="NFC"))
    # Decomposed e + U+0301 combining acute → NFC → é → encodable in cp437
    decomposed = "é"  # explicitly two code points
    segments = engine.render_text(decomposed + "\n", fallback="auto")
    assert isinstance(segments[0], NativeTextSegment)


def test_nfc_is_applied_before_strict_check() -> None:
    engine = _make_engine_with("cp437", policy=UnicodePolicy(normalize="NFC"))
    # Decomposed é would fail encoding test without normalization
    decomposed = "é\n"
    # After NFC it becomes encodable — strict should not raise
    segments = engine.render_text(decomposed, fallback="strict")
    assert isinstance(segments[0], NativeTextSegment)


def test_transliterate_makes_accented_text_native() -> None:
    engine = _make_engine_with("ascii", policy=UnicodePolicy(transliterate=True))
    segments = engine.render_text("café\n", fallback="strict")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"cafe" in segments[0].data


def test_transliterate_drops_non_latin_silently() -> None:
    engine = _make_engine_with("ascii", policy=UnicodePolicy(transliterate=True))
    # Greek has no ASCII equivalent — dropped entirely, not replaced
    segments = engine.render_text("λ\n", fallback="native")
    assert isinstance(segments[0], NativeTextSegment)
    assert b"\xce\xbb" not in segments[0].data  # no UTF-8 lambda bytes


def test_normalize_none_does_not_compose() -> None:
    engine = _make_engine_with("cp437", policy=UnicodePolicy(normalize="none"))
    # Decomposed form stays decomposed — combining char may not be encodable
    decomposed = "é\n"  # e + combining acute, not pre-composed
    # Under normalize=none this may rasterize or raise depending on codepage
    # The important thing is it does not crash and returns segments
    segments = engine.render_text(decomposed, fallback="auto")
    assert len(segments) >= 1


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


def test_wrap_does_not_produce_empty_segments() -> None:
    engine = make_engine("cp437")
    segments = engine.render_text("word " * 20 + "\n", fallback="raster", wrap=True)
    assert all(len(s.image.data) > 0 for s in segments if isinstance(s, RasterTextSegment))


# ---------------------------------------------------------------------------
# Wrapping — native
# ---------------------------------------------------------------------------

def test_wrap_native_splits_by_column_count() -> None:
    metrics = NativeFontMetrics(columns_normal=10, columns_double_width=5)
    engine = _make_engine_with("cp437", metrics=metrics)
    # 25 chars → 3 lines of ≤10 chars each
    segments = engine.render_text("A" * 25 + "\n", wrap=True)
    assert len(segments) == 3
    assert all(isinstance(s, NativeTextSegment) for s in segments)


def test_wrap_native_exact_column_boundary() -> None:
    metrics = NativeFontMetrics(columns_normal=10, columns_double_width=5)
    engine = _make_engine_with("cp437", metrics=metrics)
    # Exactly 10 chars → 1 line, no wrap
    segments = engine.render_text("A" * 10 + "\n", wrap=True)
    assert len(segments) == 1


def test_wrap_native_without_metrics_passthrough() -> None:
    engine = make_engine("cp437")
    line = "A" * 200 + "\n"
    segments = engine.render_text(line, wrap=True)
    # No NativeFontMetrics → passes through unchanged
    assert len(segments) == 1
