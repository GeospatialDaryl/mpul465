from __future__ import annotations

from mpul465.constants import Alignment, BarcodeKind, ESC, GS, LF
from mpul465.models import MonoRaster


class CommandEncoder:
    """Generates ESC/POS byte sequences.

    Every method returns bytes and never writes to a transport.
    This makes command encoding purely functional and hardware-free to test.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bytes:
        return ESC + b"@"

    # ------------------------------------------------------------------
    # Paper feed
    # ------------------------------------------------------------------

    def line_feed(self) -> bytes:
        return LF

    def feed_lines(self, lines: int) -> bytes:
        if not 0 <= lines <= 255:
            raise ValueError(f"lines must be 0–255, got {lines}")
        return ESC + b"d" + bytes([lines])

    # ------------------------------------------------------------------
    # Text formatting
    # ------------------------------------------------------------------

    def bold(self, enabled: bool) -> bytes:
        return ESC + b"E" + bytes([1 if enabled else 0])

    def underline(self, enabled: bool) -> bytes:
        return ESC + b"-" + bytes([1 if enabled else 0])

    def align(self, mode: Alignment) -> bytes:
        value = {Alignment.LEFT: 0, Alignment.CENTER: 1, Alignment.RIGHT: 2}[mode]
        return ESC + b"a" + bytes([value])

    # ------------------------------------------------------------------
    # Text data
    # ------------------------------------------------------------------

    def text_bytes(self, data: bytes) -> bytes:
        return data

    # ------------------------------------------------------------------
    # Raster graphics
    # ------------------------------------------------------------------

    def raster_image(self, image: MonoRaster) -> bytes:
        # GS v 0 — raster bit image transfer
        # Format: GS v 0 m xL xH yL yH [data]
        # m=0: normal density
        x_bytes = image.stride
        y_bytes = image.height
        xL = x_bytes & 0xFF
        xH = (x_bytes >> 8) & 0xFF
        yL = y_bytes & 0xFF
        yH = (y_bytes >> 8) & 0xFF
        header = GS + b"v0" + bytes([0, xL, xH, yL, yH])
        return header + image.data

    # ------------------------------------------------------------------
    # Barcodes / QR  (command details to be verified on hardware)
    # ------------------------------------------------------------------

    def qr(self, value: str) -> bytes:
        raise NotImplementedError("QR command format must be verified on hardware")

    def barcode(self, value: str, kind: BarcodeKind) -> bytes:
        raise NotImplementedError("Barcode command format must be verified on hardware")
