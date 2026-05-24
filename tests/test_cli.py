from __future__ import annotations

import argparse
import io
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from mpul465.cli import (
    _hex_dump,
    _make_config,
    _make_transport,
    cmd_dump,
    cmd_print_image,
    cmd_print_svg,
    cmd_print_text,
)
from mpul465.transports.dry_run import DryRunTransport


def _base_namespace(**overrides: object) -> argparse.Namespace:
    defaults = dict(
        port="/dev/ttyUSB0",
        baudrate=115200,
        dots=64,
        codepage="cp437",
        feed=0,
        dump_bytes=True,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# _make_config
# ---------------------------------------------------------------------------

def test_make_config_uses_dots_and_codepage() -> None:
    args = _base_namespace(dots=200, codepage="ascii")
    cfg = _make_config(args)
    assert cfg.dots_per_line == 200
    assert cfg.native_codepage == "ascii"


# ---------------------------------------------------------------------------
# _make_transport
# ---------------------------------------------------------------------------

def test_make_transport_returns_dry_run_when_flag_set() -> None:
    args = _base_namespace(dump_bytes=True)
    transport = _make_transport(args)
    assert isinstance(transport, DryRunTransport)


# ---------------------------------------------------------------------------
# _hex_dump
# ---------------------------------------------------------------------------

def test_hex_dump_prints_correct_columns(capsys: pytest.CaptureFixture[str]) -> None:
    _hex_dump(b"\x00\x01\x02")
    out = capsys.readouterr().out
    assert "00 01 02" in out
    assert "0000" in out  # address column


def test_hex_dump_replaces_non_printable_with_dot(capsys: pytest.CaptureFixture[str]) -> None:
    _hex_dump(b"\x00A\xff")
    out = capsys.readouterr().out
    assert "." in out
    assert "A" in out


def test_hex_dump_handles_empty_input(capsys: pytest.CaptureFixture[str]) -> None:
    _hex_dump(b"")
    out = capsys.readouterr().out
    assert out == ""


def test_hex_dump_wraps_at_16_bytes(capsys: pytest.CaptureFixture[str]) -> None:
    _hex_dump(bytes(32))
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 2
    assert lines[1].startswith("0010")


# ---------------------------------------------------------------------------
# cmd_print_text
# ---------------------------------------------------------------------------

def test_cmd_print_text_dry_run_returns_zero() -> None:
    args = _base_namespace(text="Hello\n", fallback="auto")
    rc = cmd_print_text(args)
    assert rc == 0


def test_cmd_print_text_output_contains_text_bytes(capsys: pytest.CaptureFixture[str]) -> None:
    args = _base_namespace(text="Hi\n", fallback="auto")
    cmd_print_text(args)
    out = capsys.readouterr().out
    # "Hi" → 0x48 0x69 in hex dump
    assert "48" in out and "69" in out


def test_cmd_print_text_with_feed(capsys: pytest.CaptureFixture[str]) -> None:
    args = _base_namespace(text="Hi\n", fallback="auto", feed=3)
    cmd_print_text(args)
    out = capsys.readouterr().out
    # ESC d 3 → 1b 64 03
    assert "1b" in out and "64" in out and "03" in out


# ---------------------------------------------------------------------------
# cmd_print_image
# ---------------------------------------------------------------------------

def test_cmd_print_image_dry_run_returns_zero(tmp_path: Path) -> None:
    img = Image.new("1", (32, 10), 0)
    img_path = tmp_path / "test.png"
    img.save(img_path)
    args = _base_namespace(image=str(img_path), width=None)
    rc = cmd_print_image(args)
    assert rc == 0


def test_cmd_print_image_width_digit_string_converted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    img = Image.new("1", (32, 4), 0)
    img_path = tmp_path / "test.png"
    img.save(img_path)
    args = _base_namespace(image=str(img_path), width="32")
    rc = cmd_print_image(args)
    assert rc == 0


# ---------------------------------------------------------------------------
# cmd_print_svg
# ---------------------------------------------------------------------------

_SIMPLE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="16">'
    b'<rect width="32" height="16" fill="black"/>'
    b"</svg>"
)


def test_cmd_print_svg_dry_run_returns_zero(tmp_path: Path) -> None:
    svg_path = tmp_path / "test.svg"
    svg_path.write_bytes(_SIMPLE_SVG)
    args = _base_namespace(svg=str(svg_path), width=None)
    rc = cmd_print_svg(args)
    assert rc == 0


def test_cmd_print_svg_produces_hex_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    svg_path = tmp_path / "test.svg"
    svg_path.write_bytes(_SIMPLE_SVG)
    args = _base_namespace(svg=str(svg_path), width=None)
    cmd_print_svg(args)
    out = capsys.readouterr().out
    # GS v 0 → 1d 76 30 should appear in the hex dump
    assert "1d" in out
    assert "76" in out


# ---------------------------------------------------------------------------
# cmd_dump
# ---------------------------------------------------------------------------

def test_cmd_dump_routes_print_text() -> None:
    args = _base_namespace(text="Hi\n", fallback="auto", dump_subcmd="print-text")
    rc = cmd_dump(args)
    assert rc == 0


def test_cmd_dump_routes_print_image(tmp_path: Path) -> None:
    img = Image.new("1", (32, 4), 0)
    img_path = tmp_path / "t.png"
    img.save(img_path)
    args = _base_namespace(image=str(img_path), width=None, dump_subcmd="print-image")
    rc = cmd_dump(args)
    assert rc == 0


def test_cmd_dump_unknown_subcmd_returns_2() -> None:
    args = _base_namespace(dump_subcmd="unknown-cmd")
    rc = cmd_dump(args)
    assert rc == 2
