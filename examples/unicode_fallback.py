"""Demonstrate automatic Unicode fallback modes."""
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.text("--- Unicode fallback demo ---\n")
    printer.text("ASCII:  Hello, world!\n")           # native
    printer.text("Latin:  Café, naïve\n")             # native in cp437
    printer.text("Auto:   λ = wavelength\n")           # raster fallback
    printer.text("Auto:   Temperature ⚙\n")           # raster fallback
    printer.text("Raster: forced raster\n", fallback="raster")
    printer.feed(3)
