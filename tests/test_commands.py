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
