from __future__ import annotations

import argparse
import sys

from mpul465.config import MPUL465Config
from mpul465.constants import BarcodeKind, TextFallbackMode
from mpul465.exceptions import MPUL465Error
from mpul465.printer import MPUL465Printer
from mpul465.transports.dry_run import DryRunTransport
from mpul465.transports.serial import SerialTransport

_VERSION = "0.5.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(args: argparse.Namespace) -> MPUL465Config:
    return MPUL465Config(
        dots_per_line=args.dots,
        native_codepage=args.codepage,
    )


def _make_transport(args: argparse.Namespace) -> SerialTransport | DryRunTransport:
    if getattr(args, "dump_bytes", False):
        return DryRunTransport()
    return SerialTransport(args.port, baudrate=args.baudrate)


def _resolve_width(raw: str | None) -> int | str | None:
    if raw is None:
        return None
    if raw == "fit":
        return "fit"
    if raw.isdigit():
        return int(raw)
    return raw


def _hex_dump(data: bytes) -> None:
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        print(f"{i:04x}  {hex_part:<47}  {asc_part}")


def _maybe_hex_dump(transport: SerialTransport | DryRunTransport) -> None:
    if isinstance(transport, DryRunTransport):
        _hex_dump(transport.buffer)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_print_text(args: argparse.Namespace) -> int:
    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        printer.text(args.text, fallback=args.fallback)
        if args.feed:
            printer.feed(args.feed)
    _maybe_hex_dump(transport)
    return 0


def cmd_print_image(args: argparse.Namespace) -> int:
    from pathlib import Path

    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        printer.image(Path(args.image), width=_resolve_width(args.width))
        if args.feed:
            printer.feed(args.feed)
    _maybe_hex_dump(transport)
    return 0


def cmd_print_svg(args: argparse.Namespace) -> int:
    from pathlib import Path

    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        printer.svg(Path(args.svg), width=_resolve_width(args.width))
        if args.feed:
            printer.feed(args.feed)
    _maybe_hex_dump(transport)
    return 0


def cmd_print_qr(args: argparse.Namespace) -> int:
    transport = _make_transport(args)
    cfg = _make_config(args)
    if getattr(args, "raster", False):
        from mpul465 import MPUL465Config as _Cfg
        cfg = _Cfg(
            dots_per_line=cfg.dots_per_line,
            native_codepage=cfg.native_codepage,
            enable_native_qr=False,
        )
    with MPUL465Printer(transport, config=cfg) as printer:
        printer.initialize()
        printer.qr(args.data)
        if args.feed:
            printer.feed(args.feed)
    _maybe_hex_dump(transport)
    return 0


def cmd_self_test(args: argparse.Namespace) -> int:
    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.print_diagnostics()
    _maybe_hex_dump(transport)
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    args.dump_bytes = True
    subcmd = args.dump_subcmd
    if subcmd == "print-text":
        return cmd_print_text(args)
    if subcmd == "print-image":
        return cmd_print_image(args)
    print(f"Unknown dump subcommand: {subcmd}", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# Argument parser helpers
# ---------------------------------------------------------------------------

def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--port", default="/dev/ttyUSB0",
        metavar="DEV", help="Serial device (default: /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--baudrate", type=int, default=115200,
        metavar="RATE", help="Serial baud rate (default: 115200)",
    )
    parser.add_argument(
        "--dots", type=int, default=384, dest="dots",
        metavar="N", help="Print width in dots (default: 384; verify on hardware)",
    )
    parser.add_argument(
        "--codepage", default="cp437",
        metavar="CP", help="Native code page (default: cp437)",
    )


def _add_width(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--width", default=None,
        metavar="N|fit", help="Output width: integer dots, 'fit' (scale to print width), or omit for natural size",
    )


def _add_feed(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--feed", type=int, default=0,
        metavar="N", help="Feed N lines after printing",
    )


def _add_dump(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dump-bytes", action="store_true",
        help="Print hex dump instead of sending to printer",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mpul465",
        description="MPU-L465 thermal printer driver CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exit codes:\n"
            "  0  success\n"
            "  1  printer or render error\n"
            "  2  usage error\n"
            "130  interrupted (Ctrl-C)"
        ),
    )
    parser.add_argument("--version", action="version", version=f"mpul465 {_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    # print-text
    p_text = sub.add_parser("print-text", help="Print a text string")
    _add_common(p_text)
    _add_feed(p_text)
    _add_dump(p_text)
    p_text.add_argument("text", help="Text to print (use \\n for newlines)")
    p_text.add_argument(
        "--fallback", default=TextFallbackMode.AUTO,
        choices=list(TextFallbackMode),
        help="Unicode fallback mode (default: auto)",
    )
    p_text.set_defaults(func=cmd_print_text)

    # print-image
    p_img = sub.add_parser("print-image", help="Print a raster image (PNG, JPEG, BMP, TIFF)")
    _add_common(p_img)
    _add_width(p_img)
    _add_feed(p_img)
    _add_dump(p_img)
    p_img.add_argument("image", help="Path to image file")
    p_img.set_defaults(func=cmd_print_image)

    # print-svg
    p_svg = sub.add_parser("print-svg", help="Print an SVG file (requires mpul465[svg])")
    _add_common(p_svg)
    _add_width(p_svg)
    _add_feed(p_svg)
    _add_dump(p_svg)
    p_svg.add_argument("svg", help="Path to SVG file")
    p_svg.set_defaults(func=cmd_print_svg)

    # print-qr
    p_qr = sub.add_parser("print-qr", help="Print a QR code")
    _add_common(p_qr)
    _add_feed(p_qr)
    _add_dump(p_qr)
    p_qr.add_argument("data", help="Data to encode in the QR code")
    p_qr.add_argument(
        "--raster", action="store_true",
        help="Force raster QR fallback (requires mpul465[barcodes]); default: native command",
    )
    p_qr.set_defaults(func=cmd_print_qr)

    # self-test
    p_test = sub.add_parser("self-test", help="Print diagnostic page to verify printer connection")
    _add_common(p_test)
    _add_feed(p_test)
    _add_dump(p_test)
    p_test.set_defaults(func=cmd_self_test)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except MPUL465Error as exc:
        print(f"mpul465: error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
