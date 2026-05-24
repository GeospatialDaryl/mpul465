from __future__ import annotations

import argparse
import sys

from mpul465.config import MPUL465Config
from mpul465.constants import TextFallbackMode
from mpul465.printer import MPUL465Printer
from mpul465.transports.dry_run import DryRunTransport
from mpul465.transports.serial import SerialTransport


def _make_config(args: argparse.Namespace) -> MPUL465Config:
    return MPUL465Config(
        dots_per_line=args.dots,
        native_codepage=args.codepage,
    )


def _make_transport(args: argparse.Namespace) -> SerialTransport | DryRunTransport:
    if getattr(args, "dump_bytes", False):
        return DryRunTransport()
    return SerialTransport(args.port, baudrate=args.baudrate)


def cmd_print_text(args: argparse.Namespace) -> int:
    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        printer.text(args.text, fallback=args.fallback)
        if args.feed:
            printer.feed(args.feed)
    if isinstance(transport, DryRunTransport):
        _hex_dump(transport.buffer)
    return 0


def cmd_print_image(args: argparse.Namespace) -> int:
    from pathlib import Path

    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        width: int | str | None = args.width
        if width and width.isdigit():
            width = int(width)
        printer.image(Path(args.image), width=width)
        if args.feed:
            printer.feed(args.feed)
    if isinstance(transport, DryRunTransport):
        _hex_dump(transport.buffer)
    return 0


def cmd_print_svg(args: argparse.Namespace) -> int:
    from pathlib import Path

    transport = _make_transport(args)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.initialize()
        width: int | str | None = args.width
        if width and width.isdigit():
            width = int(width)
        printer.svg(Path(args.svg), width=width)
        if args.feed:
            printer.feed(args.feed)
    if isinstance(transport, DryRunTransport):
        _hex_dump(transport.buffer)
    return 0


def cmd_self_test(args: argparse.Namespace) -> int:
    transport = SerialTransport(args.port, baudrate=args.baudrate)
    with MPUL465Printer(transport, config=_make_config(args)) as printer:
        printer.print_diagnostics()
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


def _hex_dump(data: bytes) -> None:
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        print(f"{i:04x}  {hex_part:<47}  {asc_part}")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial device path")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--dots", type=int, default=384, dest="dots", help="Print width in dots")
    parser.add_argument("--codepage", default="cp437")


def main() -> None:
    parser = argparse.ArgumentParser(prog="mpul465", description="MPU-L465 thermal printer tool")
    sub = parser.add_subparsers(dest="command", required=True)

    # print-text
    p_text = sub.add_parser("print-text", help="Print a text string")
    _add_common(p_text)
    p_text.add_argument("text")
    p_text.add_argument("--fallback", default=TextFallbackMode.AUTO,
                        choices=list(TextFallbackMode))
    p_text.add_argument("--feed", type=int, default=0)
    p_text.add_argument("--dump-bytes", action="store_true")
    p_text.set_defaults(func=cmd_print_text)

    # print-image
    p_img = sub.add_parser("print-image", help="Print a raster image")
    _add_common(p_img)
    p_img.add_argument("image")
    p_img.add_argument("--width", default=None)
    p_img.add_argument("--feed", type=int, default=0)
    p_img.add_argument("--dump-bytes", action="store_true")
    p_img.set_defaults(func=cmd_print_image)

    # print-svg
    p_svg = sub.add_parser("print-svg", help="Print an SVG file")
    _add_common(p_svg)
    p_svg.add_argument("svg")
    p_svg.add_argument("--width", default=None)
    p_svg.add_argument("--feed", type=int, default=0)
    p_svg.add_argument("--dump-bytes", action="store_true")
    p_svg.set_defaults(func=cmd_print_svg)

    # self-test
    p_test = sub.add_parser("self-test", help="Print diagnostic page")
    _add_common(p_test)
    p_test.add_argument("--feed", type=int, default=0)
    p_test.set_defaults(func=cmd_self_test)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
