from __future__ import annotations

import logging
import math

from PIL import Image, ImageDraw

from mpul465.config import MPUL465Config
from mpul465.constants import Alignment, TextFallbackMode
from mpul465.exceptions import UnsupportedCharacterError
from mpul465.models import MonoRaster, NativeTextSegment, PrintSegment, RasterTextSegment
from mpul465.text.codepages import CodePage
from mpul465.text.fonts import FontRegistry

logger = logging.getLogger(__name__)


class TextRasterizer:
    """Renders a text string to a MonoRaster using Pillow."""

    def __init__(self, font_registry: FontRegistry, config: MPUL465Config) -> None:
        self._fonts = font_registry
        self._config = config

    def render_line(
        self,
        text: str,
        *,
        width: int,
        align: Alignment = Alignment.LEFT,
        font_size: int | None = None,
    ) -> MonoRaster:
        size = font_size or self._config.default_font_size
        font = self._fonts.resolve(size)

        # Measure text height
        dummy = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        height = max(text_h + 4, size + 4)

        # Compute x offset for alignment
        if align == Alignment.CENTER:
            x = max(0, (width - text_w) // 2)
        elif align == Alignment.RIGHT:
            x = max(0, width - text_w)
        else:
            x = 0

        img = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(img)
        draw.text((x, 2), text, font=font, fill=0)

        mono = img.convert("1", dither=Image.Dither.NONE)
        stride = math.ceil(width / 8)
        raw = mono.tobytes()
        return MonoRaster(width=width, height=height, data=raw, stride=stride)


class TextEngine:
    """Decides native vs. raster rendering per line and returns PrintSegment lists."""

    def __init__(
        self,
        codepage: CodePage,
        rasterizer: TextRasterizer,
        config: MPUL465Config,
    ) -> None:
        self._codepage = codepage
        self._rasterizer = rasterizer
        self._config = config

    def render_text(
        self, text: str, *, fallback: str = TextFallbackMode.AUTO
    ) -> list[PrintSegment]:
        segments: list[PrintSegment] = []
        for line in self._split_lines(text):
            segments.extend(self._render_line(line, fallback=fallback))
        return segments

    def _split_lines(self, text: str) -> list[str]:
        """Split on newlines, preserving the newline on each chunk."""
        parts = text.split("\n")
        if parts and parts[-1] == "":
            parts = parts[:-1]
        return [part + "\n" for part in parts]

    def _render_line(self, line: str, *, fallback: str) -> list[PrintSegment]:
        mode = TextFallbackMode(fallback)

        if mode == TextFallbackMode.RASTER:
            return [self._rasterize(line)]

        unsupported = self._codepage.unsupported_chars(line)

        if mode == TextFallbackMode.STRICT and unsupported:
            raise UnsupportedCharacterError(
                f"Text contains characters not encodable in {self._codepage.name}",
                characters=unsupported,
                fallback=fallback,
            )

        if mode in (TextFallbackMode.AUTO, TextFallbackMode.NATIVE) and not unsupported:
            return [NativeTextSegment(data=self._codepage.encode(line))]

        if mode == TextFallbackMode.AUTO and unsupported:
            logger.warning(
                "Raster fallback for %d unsupported character(s): %s",
                len(unsupported),
                unsupported,
            )
            return [self._rasterize(line)]

        # NATIVE mode with unsupported chars: replace with policy character
        cleaned = "".join(
            ch if ch not in unsupported else "?" for ch in line
        )
        return [NativeTextSegment(data=self._codepage.encode(cleaned))]

    def _rasterize(self, text: str) -> RasterTextSegment:
        raster = self._rasterizer.render_line(
            text.rstrip("\n"),
            width=self._config.dots_per_line,
        )
        return RasterTextSegment(image=raster)
