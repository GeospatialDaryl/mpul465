from __future__ import annotations

import logging
from pathlib import Path

from PIL import ImageFont

logger = logging.getLogger(__name__)

_SYSTEM_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


class FontRegistry:
    """Resolves PIL FreeType fonts by size, searching system font paths."""

    def __init__(self, default_font: Path | None = None) -> None:
        self._default_font = default_font or self._find_system_font()

    def resolve(self, size: int) -> ImageFont.FreeTypeFont:
        if self._default_font is None:
            logger.warning("No TrueType font found; falling back to PIL default bitmap font")
            return ImageFont.load_default()  # type: ignore[return-value]
        return ImageFont.truetype(str(self._default_font), size=size)

    @staticmethod
    def _find_system_font() -> Path | None:
        for candidate in _SYSTEM_FONT_CANDIDATES:
            p = Path(candidate)
            if p.exists():
                return p
        return None
