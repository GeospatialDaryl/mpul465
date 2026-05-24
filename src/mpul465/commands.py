from __future__ import annotations

from mpul465.constants import Alignment, BarcodeKind, ESC, GS, LF
from mpul465.models import MonoRaster

# GS k function-B barcode type IDs (ESC/POS standard; verify on hardware)
_BARCODE_KIND_ID: dict[BarcodeKind, int] = {
    BarcodeKind.UPCA: 65,
    BarcodeKind.EAN13: 67,
    BarcodeKind.EAN8: 68,
    BarcodeKind.CODE39: 69,
    BarcodeKind.CODE128: 73,
}

# GS ( k QR error-correction level bytes (ESC/POS standard; verify on hardware)
_QR_EC_BYTE: dict[str, int] = {"L": 48, "M": 49, "Q": 50, "H": 51}


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
    # Barcodes / QR  (standard ESC/POS format; verify exact bytes on hardware)
    # ------------------------------------------------------------------

    def qr(
        self,
        value: str,
        *,
        module_size: int = 3,
        error_correction: str = "M",
    ) -> bytes:
        # GS ( k QR code sequence (Epson-compatible ESC/POS format).
        # Byte sequence must be verified on the MPU-L465 before trusting output.
        ec = _QR_EC_BYTE.get(error_correction.upper())
        if ec is None:
            raise ValueError(f"error_correction must be L/M/Q/H, got {error_correction!r}")
        if not 1 <= module_size <= 16:
            raise ValueError(f"module_size must be 1–16, got {module_size}")

        data = value.encode("ascii")
        data_len = len(data) + 3
        pL = data_len & 0xFF
        pH = (data_len >> 8) & 0xFF

        out = bytearray()
        out += GS + b"(k" + bytes([3, 0, 49, 67, module_size])   # set size
        out += GS + b"(k" + bytes([3, 0, 49, 69, ec])             # set EC level
        out += GS + b"(k" + bytes([pL, pH, 49, 80, 48]) + data   # store data
        out += GS + b"(k" + bytes([3, 0, 49, 81, 48])             # print
        return bytes(out)

    def barcode(self, value: str, kind: BarcodeKind) -> bytes:
        # GS k function-B barcode command (ESC/POS standard).
        # Supported types and exact format must be verified on the MPU-L465.
        m = _BARCODE_KIND_ID[kind]
        data = value.encode("ascii")
        n = len(data)
        return GS + b"k" + bytes([m, n]) + data
