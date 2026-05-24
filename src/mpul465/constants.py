from __future__ import annotations

from enum import StrEnum

# ESC/POS byte prefixes
ESC = b"\x1b"
GS = b"\x1d"
LF = b"\x0a"


class Alignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TextFallbackMode(StrEnum):
    AUTO = "auto"
    NATIVE = "native"
    RASTER = "raster"
    STRICT = "strict"


class BarcodeKind(StrEnum):
    CODE128 = "code128"
    CODE39 = "code39"
    EAN13 = "ean13"
    EAN8 = "ean8"
    UPCA = "upca"
