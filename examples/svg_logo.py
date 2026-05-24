"""Print an SVG file scaled to full paper width. Requires mpul465[svg]."""
import sys
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

svg_path = sys.argv[1] if len(sys.argv) > 1 else "logo.svg"

with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.svg(svg_path, width="fit")
    printer.feed(3)
