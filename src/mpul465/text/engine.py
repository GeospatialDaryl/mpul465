from __future__ import annotations

import logging
import math

from PIL import Image, ImageDraw

from mpul465.config import MPUL465Config
from mpul465.constants import Alignment, TextFallbackMode
from mpul465.exceptions import UnsupportedCharacterError
from mpul465.models import MonoRaster, NativeTextSegment, PrintSegment, RasterTextSegment
from mpul465.text.codepages import CodePage, UnicodePolicy
from mpul465.text.fonts import FontRegistry
from mpul465.text.wrapping import NativeFontMetrics, wrap_native, wrap_raster

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

        dummy = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_h = bbox[3] - bbox[1]
        text_w = bbox[2] - bbox[0]
        height = max(text_h + 4, size + 4)

        if align == Alignment.CENTER:
            x = max(0, (width - text_w) // 2)
        elif align == Alignment.RIGHT:
            x = max(0, width - text_w)
        else:
            x = 0

        img = Image.new("L", (width, height), 255)
        ImageDraw.Draw(img).text((x, 2), text, font=font, fill=0)

        mono = img.convert("1", dither=Image.Dither.NONE)
        stride = math.ceil(width / 8)
        return MonoRaster(width=width, height=height, data=mono.tobytes(), stride=stride)

    def measure_width_px(self, text: str, font_size: int | None = None) -> int:
        """Return the rendered pixel width of text at the given font size."""
        size = font_size or self._config.default_font_size
        font = self._fonts.resolve(size)
        dummy = Image.new("L", (1, 1))
        bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]


class TextEngine:
    """Decides native vs. raster rendering per line and returns PrintSegment lists."""

    def __init__(
        self,
        codepage: CodePage,
        rasterizer: TextRasterizer,
        config: MPUL465Config,
        *,
        unicode_policy: UnicodePolicy | None = None,
        native_font_metrics: NativeFontMetrics | None = None,
    ) -> None:
        self._codepage = codepage
        self._rasterizer = rasterizer
        self._config = config
        self._policy = unicode_policy or UnicodePolicy()
        self._native_metrics = native_font_metrics

    def render_text(
        self,
        text: str,
        *,
        fallback: str = TextFallbackMode.AUTO,
        wrap: bool = False,
    ) -> list[PrintSegment]:
        segments: list[PrintSegment] = []
        for line in self._split_lines(text):
            for wrapped in self._maybe_wrap(line, fallback=fallback, wrap=wrap):
                segments.extend(self._render_line(wrapped, fallback=fallback))
        return segments

    # ------------------------------------------------------------------
    # Splitting and wrapping
    # ------------------------------------------------------------------

    def _split_lines(self, text: str) -> list[str]:
        """Split on newlines, preserving the trailing newline on each chunk."""
        parts = text.split("\n")
        if parts and parts[-1] == "":
            parts = parts[:-1]
        return [part + "\n" for part in parts]

    def _maybe_wrap(self, line: str, *, fallback: str, wrap: bool) -> list[str]:
        if not wrap:
            return [line]

        mode = TextFallbackMode(fallback)
        will_raster = (
            mode == TextFallbackMode.RASTER
            or (mode == TextFallbackMode.AUTO and bool(self._codepage.unsupported_chars(line)))
        )

        if will_raster:
            return self._wrap_raster(line)
        return self._wrap_native(line)

    def _wrap_native(self, line: str) -> list[str]:
        if self._native_metrics is not None:
            return wrap_native(line, self._native_metrics)
        # No metrics configured — pass through; wrapping requires hardware verification first.
        return [line]

    def _wrap_raster(self, line: str) -> list[str]:
        size = self._config.default_font_size
        font = self._rasterizer._fonts.resolve(size)
        return wrap_raster(
            line.rstrip("\n"),
            width_px=self._config.dots_per_line,
            font=font,
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_line(self, line: str, *, fallback: str) -> list[PrintSegment]:
        # Apply Unicode normalization/transliteration before encoding test
        normalized = self._policy.apply(line)
        mode = TextFallbackMode(fallback)

        if mode == TextFallbackMode.RASTER:
            return [self._rasterize(normalized)]

        unsupported = self._codepage.unsupported_chars(normalized)

        if mode == TextFallbackMode.STRICT and unsupported:
            raise UnsupportedCharacterError(
                f"Text contains characters not encodable in {self._codepage.name}",
                characters=unsupported,
                fallback=fallback,
            )

        if not unsupported:
            return [NativeTextSegment(data=self._codepage.encode(normalized))]

        if mode == TextFallbackMode.AUTO:
            logger.warning(
                "Raster fallback for %d unsupported character(s): %s",
                len(unsupported),
                unsupported,
            )
            return [self._rasterize(normalized)]

        # NATIVE mode: replace unsupported chars with policy replacement character
        cleaned = "".join(
            ch if ch not in unsupported else self._policy.replacement for ch in normalized
        )
        return [NativeTextSegment(data=self._codepage.encode(cleaned))]

    def _rasterize(self, text: str) -> RasterTextSegment:
        raster = self._rasterizer.render_line(
            text.rstrip("\n"),
            width=self._config.dots_per_line,
        )
        return RasterTextSegment(image=raster)
