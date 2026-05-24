from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonoRaster:
    """1-bit packed image passed between the graphics layer and CommandEncoder.

    stride = ceil(width / 8) bytes per row.
    data = packed rows, MSB-first by default.
    """

    width: int
    height: int
    data: bytes
    stride: int


@dataclass(frozen=True, slots=True)
class NativeTextSegment:
    """Text encodable in the printer's native code page; ready to send as bytes."""

    data: bytes


@dataclass(frozen=True, slots=True)
class RasterTextSegment:
    """Text that must be rendered as a raster image."""

    image: MonoRaster


PrintSegment = NativeTextSegment | RasterTextSegment
