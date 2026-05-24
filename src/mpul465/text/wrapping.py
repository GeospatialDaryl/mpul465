from __future__ import annotations

from dataclasses import dataclass

from PIL import ImageFont


@dataclass(frozen=True, slots=True)
class NativeFontMetrics:
    """Column counts for the printer's native text font modes.

    Values depend on the active printer font and must be verified on hardware.
    """

    columns_normal: int
    columns_double_width: int


def wrap_native(text: str, metrics: NativeFontMetrics) -> list[str]:
    """Wrap text by native column count."""
    cols = metrics.columns_normal
    lines: list[str] = []
    for paragraph in text.splitlines(keepends=True):
        stripped = paragraph.rstrip("\n")
        for i in range(0, max(len(stripped), 1), cols):
            chunk = stripped[i : i + cols]
            lines.append(chunk + "\n")
    return lines


def wrap_raster(text: str, *, width_px: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """Wrap text by pixel width using font measurement."""
    words = text.split()
    if not words:
        return ["\n"]

    lines: list[str] = []
    current: list[str] = []

    for word in words:
        trial = " ".join(current + [word])
        bbox = font.getbbox(trial)
        if bbox[2] - bbox[0] <= width_px:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current) + "\n")
            current = [word]

    if current:
        lines.append(" ".join(current) + "\n")

    return lines
