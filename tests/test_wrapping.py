from __future__ import annotations

from mpul465.text.fonts import FontRegistry
from mpul465.text.wrapping import NativeFontMetrics, wrap_native, wrap_raster


# ---------------------------------------------------------------------------
# wrap_native — direct tests
# ---------------------------------------------------------------------------

def _metrics(cols: int = 10) -> NativeFontMetrics:
    return NativeFontMetrics(columns_normal=cols, columns_double_width=cols // 2)


def test_wrap_native_empty_string_returns_empty_list() -> None:
    assert wrap_native("", _metrics()) == []


def test_wrap_native_text_shorter_than_columns_stays_one_line() -> None:
    result = wrap_native("Hello\n", _metrics(20))
    assert result == ["Hello\n"]


def test_wrap_native_text_at_exact_column_boundary_stays_one_line() -> None:
    result = wrap_native("A" * 10 + "\n", _metrics(10))
    assert result == ["A" * 10 + "\n"]


def test_wrap_native_text_one_over_boundary_splits_to_two() -> None:
    result = wrap_native("A" * 11 + "\n", _metrics(10))
    assert len(result) == 2
    assert result[0] == "A" * 10 + "\n"
    assert result[1] == "A\n"


def test_wrap_native_splits_long_line_into_chunks() -> None:
    result = wrap_native("A" * 25 + "\n", _metrics(10))
    assert len(result) == 3
    assert result[0] == "A" * 10 + "\n"
    assert result[1] == "A" * 10 + "\n"
    assert result[2] == "A" * 5 + "\n"


def test_wrap_native_newline_only_produces_one_line() -> None:
    result = wrap_native("\n", _metrics(10))
    assert result == ["\n"]


def test_wrap_native_multi_paragraph_wraps_each_independently() -> None:
    result = wrap_native("AB\nCD\n", _metrics(3))
    assert result == ["AB\n", "CD\n"]


def test_wrap_native_each_result_ends_with_newline() -> None:
    result = wrap_native("Hello World\n", _metrics(5))
    assert all(line.endswith("\n") for line in result)


def test_wrap_native_no_trailing_newline_still_wrapped() -> None:
    result = wrap_native("Hello", _metrics(3))
    assert len(result) == 2
    assert result[0] == "Hel\n"
    assert result[1] == "lo\n"


# ---------------------------------------------------------------------------
# wrap_raster — direct tests
# ---------------------------------------------------------------------------

def _font(size: int = 12) -> object:
    return FontRegistry().resolve(size)


def test_wrap_raster_empty_string_returns_single_newline() -> None:
    font = _font()
    result = wrap_raster("", width_px=400, font=font)  # type: ignore[arg-type]
    assert result == ["\n"]


def test_wrap_raster_whitespace_only_returns_single_newline() -> None:
    font = _font()
    result = wrap_raster("   ", width_px=400, font=font)  # type: ignore[arg-type]
    assert result == ["\n"]


def test_wrap_raster_single_short_word_fits_on_one_line() -> None:
    font = _font()
    result = wrap_raster("Hi", width_px=400, font=font)  # type: ignore[arg-type]
    assert result == ["Hi\n"]


def test_wrap_raster_all_results_end_with_newline() -> None:
    font = _font()
    result = wrap_raster("word " * 20, width_px=200, font=font)  # type: ignore[arg-type]
    assert all(line.endswith("\n") for line in result)


def test_wrap_raster_long_text_produces_multiple_lines() -> None:
    font = _font()
    result = wrap_raster("word " * 20, width_px=100, font=font)  # type: ignore[arg-type]
    assert len(result) > 1


def test_wrap_raster_no_line_exceeds_width() -> None:
    font = _font(size=18)
    result = wrap_raster("word " * 20, width_px=150, font=font)  # type: ignore[arg-type]
    for line in result:
        bbox = font.getbbox(line.rstrip("\n"))  # type: ignore[union-attr]
        assert bbox[2] - bbox[0] <= 150 or len(line.split()) == 1  # single word may exceed


def test_wrap_raster_single_word_too_wide_stays_on_one_line() -> None:
    font = _font()
    long_word = "A" * 200
    result = wrap_raster(long_word, width_px=10, font=font)  # type: ignore[arg-type]
    assert len(result) == 1
    assert long_word in result[0]
