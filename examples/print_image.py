"""Print a raster image scaled to full paper width."""
import sys
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

image_path = sys.argv[1] if len(sys.argv) > 1 else "logo.png"

with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.image(image_path, width="fit")
    printer.feed(3)
