"""Basic hello world print."""
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.text("Hello from Python\n")
    printer.bold("Bold line\n")
    printer.underline("Underlined\n")
    printer.feed(3)
