from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MPUL465Config:
    """Immutable device configuration.

    dots_per_line must be verified on hardware via a calibration print.
    384 is a common 58 mm-class value but is not guaranteed for this unit.
    """

    name: str = "SII MPU-L465"
    dots_per_line: int = 384
    default_encoding: str = "ascii"
    native_codepage: str = "cp437"
    image_chunk_height: int = 24
    default_font_path: str | None = None
    default_font_size: int = 24
    enable_native_qr: bool = True
    enable_native_barcode: bool = True
    image_dither: str = "floyd-steinberg"
