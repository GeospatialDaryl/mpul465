#!/usr/bin/env python3
"""Hardware self-test for the SII MPU-L465.

Prints a structured test page that exercises every implemented feature.
Use this on first hardware contact to verify the connection, print width,
text encoding, raster pipeline, and Unicode fallback.

Usage:
    # With hardware
    python examples/self_test.py --port /dev/ttyUSB0

    # Dry run: prints hex byte dump, no printer needed
    python examples/self_test.py --dry-run

    # Override assumed print width (update after calibration)
    python examples/self_test.py --port /dev/ttyUSB0 --dots 384
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# Allow running directly without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image, ImageDraw

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.constants import Alignment
from mpul465.transports.dry_run import DryRunTransport
from mpul465.transports.serial import SerialTransport

_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Test pattern generators
# ---------------------------------------------------------------------------

def _full_black_bar(width: int, height: int = 8) -> Image.Image:
    """Solid black bar — verifies full print width."""
    return Image.new("1", (width, height), 0)


def _full_white_bar(width: int, height: int = 8) -> Image.Image:
    return Image.new("1", (width, height), 1)


def _checkerboard(width: int, height: int = 16, cell: int = 8) -> Image.Image:
    """Checkerboard pattern — verifies bit packing and MSB-first order."""
    img = Image.new("1", (width, height), 1)
    for y in range(height):
        for x in range(width):
            if (x // cell + y // cell) % 2 == 0:
                img.putpixel((x, y), 0)
    return img


def _pixel_ruler(width: int) -> Image.Image:
    """1px alternating columns — lets you count exact dot width."""
    img = Image.new("1", (width, 4), 1)
    for x in range(width):
        if x % 2 == 0:
            for y in range(4):
                img.putpixel((x, y), 0)
    return img


def _decade_ruler(width: int) -> Image.Image:
    """Tick marks every 10 and 50 dots — for measuring print width."""
    img = Image.new("1", (width, 12), 1)
    draw = ImageDraw.Draw(img)
    for x in range(0, width, 10):
        tick_h = 8 if x % 50 == 0 else 4
        draw.line([(x, 0), (x, tick_h - 1)], fill=0)
    return img


def _diagonal_gradient(width: int, height: int = 32) -> Image.Image:
    """Diagonal gradient — verifies Floyd-Steinberg dithering pipeline."""
    img = Image.new("L", (width, height))
    for y in range(height):
        for x in range(width):
            img.putpixel((x, y), int(255 * (x + y) / (width + height)))
    return img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def _border_box(width: int, height: int = 20) -> Image.Image:
    """1px border rectangle — verifies corners and edges."""
    img = Image.new("1", (width, height), 1)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=0)
    return img


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

def section_header(p: MPUL465Printer, title: str, dots: int) -> None:
    p.image(_full_black_bar(dots, 4))
    p.align(Alignment.CENTER)
    p.text(f"  {title}  \n")
    p.align(Alignment.LEFT)


def test_connection(p: MPUL465Printer, dots: int) -> None:
    p.align(Alignment.CENTER)
    p.text("MPU-L465 SELF-TEST\n")
    p.text(f"mpul465 v{_VERSION}\n")
    p.text(f"Width: {dots} dots\n")
    p.align(Alignment.LEFT)
    p.image(_full_black_bar(dots, 6))
    p.image(_full_white_bar(dots, 6))
    p.image(_full_black_bar(dots, 6))


def test_text_styles(p: MPUL465Printer) -> None:
    p.text("Normal text\n")
    p.bold("Bold text\n")
    p.underline("Underlined text\n")
    p.bold("Bold + ")
    p.text("then normal\n")


def test_alignment(p: MPUL465Printer) -> None:
    p.align(Alignment.LEFT)
    p.text("Left aligned\n")
    p.align(Alignment.CENTER)
    p.text("Center aligned\n")
    p.align(Alignment.RIGHT)
    p.text("Right aligned\n")
    p.align(Alignment.LEFT)


def test_native_codepage(p: MPUL465Printer) -> None:
    # Characters that should print natively in cp437
    p.text("ASCII:   Hello, World!\n")
    p.text("Latin:   Cafe Naif\n")
    p.text("Numbers: 0123456789\n")
    p.text("Symbols: !@#$%^&*()_+-=\n")
    p.text("Lines:   +---------+\n")
    # cp437 box-drawing (native bytes 0xC9, 0xBB, etc.)
    try:
        p.text("Box:     \xda\xc4\xc4\xc4\xbf\n", fallback="strict")
        p.text("         \xb3   \xb3\n", fallback="strict")
        p.text("         \xc0\xc4\xc4\xc4\xd9\n", fallback="strict")
    except Exception:
        p.text("Box:     [cp437 box chars]\n")


def test_unicode_fallback(p: MPUL465Printer) -> None:
    # AUTO mode — these all trigger raster fallback silently
    p.text("Degree:  72°F\n")          # °  — in cp437, should be native
    p.text("Lambda:  λ = wavelength\n")  # λ  — raster
    p.text("Pi:      π ≈ 3.14159\n") # π ≈ — raster
    p.text("Gear:    ⚙️\n")          # ⚙️ — raster
    p.text("Copy:    © 2025\n")           # ©  — check if native
    p.text("Euro:    € 4.99\n")           # €  — raster
    p.text("Greek:   ΑΒΓΔΕ\n")  # ΑΒΓΔΕ — raster
    p.text("Math:    √∞∑∫\n")         # √∞∑∫ — raster


def test_strict_rejection(p: MPUL465Printer) -> None:
    """Verify UnsupportedCharacterError fires in strict mode."""
    from mpul465.exceptions import UnsupportedCharacterError

    caught = False
    try:
        p.text("λ\n", fallback="strict")
    except UnsupportedCharacterError as exc:
        caught = True
        p.text(f"strict OK: caught {sorted(exc.characters)}\n")
    if not caught:
        p.text("strict WARN: no error raised for lambda\n")


def test_raster_patterns(p: MPUL465Printer, dots: int) -> None:
    p.text("Full-width black bar (6px):\n")
    p.image(_full_black_bar(dots, 6))

    p.text("Checkerboard (8px cells):\n")
    p.image(_checkerboard(dots, 24, 8))

    p.text("Diagonal dither gradient:\n")
    p.image(_diagonal_gradient(dots, 32))

    p.text("Border box:\n")
    p.image(_border_box(dots, 20))


def test_calibration_ruler(p: MPUL465Printer, dots: int) -> None:
    p.text(f"Pixel ruler ({dots} dots):\n")
    p.image(_pixel_ruler(dots))
    p.text("Decade ruler (ticks every 10, tall every 50):\n")
    p.image(_decade_ruler(dots))
    p.text(f"^ if ruler edge == paper edge, dots_per_line={dots} is correct\n")


def test_feed(p: MPUL465Printer) -> None:
    p.text("Feed 1: ")
    p.feed(1)
    p.text("Feed 3:\n")
    p.feed(3)
    p.text("<-- 3 blank lines above\n")


def test_width_sanity(p: MPUL465Printer, dots: int) -> None:
    """Print lines of known character counts to cross-check column width."""
    for cols in (20, 24, 32, 40, 48):
        p.text("X" * cols + f" ({cols})\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_self_test(printer: MPUL465Printer, dots: int) -> None:
    printer.initialize()

    # --- Connection ---
    section_header(printer, "CONNECTION", dots)
    test_connection(printer, dots)
    printer.feed(1)

    # --- Text styles ---
    section_header(printer, "TEXT STYLES", dots)
    test_text_styles(printer)
    printer.feed(1)

    # --- Alignment ---
    section_header(printer, "ALIGNMENT", dots)
    test_alignment(printer)
    printer.feed(1)

    # --- Native code page ---
    section_header(printer, "NATIVE CODEPAGE (cp437)", dots)
    test_native_codepage(printer)
    printer.feed(1)

    # --- Unicode fallback ---
    section_header(printer, "UNICODE FALLBACK", dots)
    test_unicode_fallback(printer)
    printer.feed(1)

    # --- Strict mode ---
    section_header(printer, "STRICT MODE", dots)
    test_strict_rejection(printer)
    printer.feed(1)

    # --- Raster patterns ---
    section_header(printer, "RASTER PATTERNS", dots)
    test_raster_patterns(printer, dots)
    printer.feed(1)

    # --- Width calibration ---
    section_header(printer, "WIDTH CALIBRATION", dots)
    test_calibration_ruler(printer, dots)
    test_width_sanity(printer, dots)
    printer.feed(1)

    # --- Feed ---
    section_header(printer, "FEED TEST", dots)
    test_feed(printer)

    # --- Footer ---
    printer.image(_full_black_bar(dots, 4))
    printer.align(Alignment.CENTER)
    printer.text("END OF SELF-TEST\n")
    printer.align(Alignment.LEFT)
    printer.feed(5)


def _hex_dump(data: bytes) -> None:
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        print(f"{i:06x}  {hex_part:<47}  {asc_part}")
    print(f"\nTotal: {len(data)} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description="MPU-L465 hardware self-test")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--dots", type=int, default=384,
                        help="Assumed print width in dots (verify with calibration ruler)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Capture bytes without sending to printer")
    args = parser.parse_args()

    if args.dry_run:
        transport: DryRunTransport | object = DryRunTransport()
        print(f"[dry run] dots_per_line={args.dots}", file=sys.stderr)
    else:
        transport = SerialTransport(args.port, baudrate=args.baudrate)
        print(f"[live] {args.port} @ {args.baudrate} baud, dots_per_line={args.dots}",
              file=sys.stderr)

    config = MPUL465Config(dots_per_line=args.dots)

    with MPUL465Printer(transport, config=config) as printer:  # type: ignore[arg-type]
        run_self_test(printer, args.dots)

    if args.dry_run and isinstance(transport, DryRunTransport):
        _hex_dump(transport.buffer)


if __name__ == "__main__":
    main()
