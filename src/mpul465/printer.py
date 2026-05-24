from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from mpul465.commands import CommandEncoder
from mpul465.config import MPUL465Config
from mpul465.constants import Alignment, BarcodeKind, TextFallbackMode
from mpul465.exceptions import CommandNotSupportedError
from mpul465.graphics import GraphicsEngine
from mpul465.graphics.packing import BitPacker
from mpul465.graphics.raster import Rasterizer
from mpul465.models import NativeTextSegment, RasterTextSegment
from mpul465.text.codepages import CodePage, UnicodePolicy
from mpul465.text.engine import TextEngine, TextRasterizer
from mpul465.text.fonts import FontRegistry
from mpul465.text.wrapping import NativeFontMetrics
from mpul465.transports.base import Transport

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_VERSION = "0.1.0"


class MPUL465Printer:
    """User-facing façade for the MPU-L465 thermal printer.

    Orchestrates transport, command encoding, text, and graphics.
    Does not contain dithering, SVG parsing, Unicode mapping, or bit packing —
    those live in their respective modules.

    Not thread-safe. One instance represents one active connection.
    """

    def __init__(
        self,
        transport: Transport,
        config: MPUL465Config | None = None,
        *,
        unicode_policy: UnicodePolicy | None = None,
        native_font_metrics: NativeFontMetrics | None = None,
    ) -> None:
        self.transport = transport
        self.config = config or MPUL465Config()
        self._commands = CommandEncoder()

        font_registry = FontRegistry(
            Path(self.config.default_font_path) if self.config.default_font_path else None
        )
        codepage = CodePage(self.config.native_codepage)
        rasterizer = TextRasterizer(font_registry, self.config)
        self._text_engine = TextEngine(
            codepage,
            rasterizer,
            self.config,
            unicode_policy=unicode_policy,
            native_font_metrics=native_font_metrics,
        )
        self._graphics = GraphicsEngine(Rasterizer(), self._commands, self.config)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> MPUL465Printer:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        self._write(self._commands.initialize())
        logger.info("Printer initialized via %s", self.transport)

    def reset(self) -> None:
        self.initialize()

    def flush(self) -> None:
        self.transport.flush()

    def close(self) -> None:
        self.transport.close()

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    def text(self, value: str, *, fallback: str = TextFallbackMode.AUTO, wrap: bool = False) -> None:
        for segment in self._text_engine.render_text(value, fallback=fallback, wrap=wrap):
            match segment:
                case NativeTextSegment(data=data):
                    self._write(self._commands.text_bytes(data))
                case RasterTextSegment(image=image):
                    self._write(self._commands.raster_image(image))

    def line(self, value: str = "") -> None:
        self.text(value + "\n")

    def bold(self, value: str) -> None:
        self._write(self._commands.bold(True))
        self.text(value)
        self._write(self._commands.bold(False))

    def underline(self, value: str) -> None:
        self._write(self._commands.underline(True))
        self.text(value)
        self._write(self._commands.underline(False))

    def align(self, mode: Alignment) -> None:
        self._write(self._commands.align(mode))

    def feed(self, lines: int = 1) -> None:
        self._write(self._commands.feed_lines(lines))

    # ------------------------------------------------------------------
    # Graphics
    # ------------------------------------------------------------------

    def image(
        self,
        image: str | Path | Image.Image,
        *,
        width: int | str | None = None,
    ) -> None:
        if isinstance(image, (str, Path)):
            pil_image = Image.open(image)
        else:
            pil_image = image
        self._write(self._graphics.image_to_commands(pil_image, width=width))

    def svg(
        self,
        svg: str | bytes | Path,
        *,
        width: int | str | None = None,
    ) -> None:
        self._write(self._graphics.svg_to_commands(svg, width=width))

    # ------------------------------------------------------------------
    # Barcodes / QR
    # ------------------------------------------------------------------

    def barcode(self, value: str, kind: BarcodeKind) -> None:
        if self.config.enable_native_barcode:
            self._write(self._commands.barcode(value, kind))
        else:
            raise CommandNotSupportedError(
                f"Native barcode is disabled (enable_native_barcode=False). "
                "Set enable_native_barcode=True once the command format is "
                "verified on hardware."
            )

    def qr(self, value: str) -> None:
        if self.config.enable_native_qr:
            self._write(self._commands.qr(value))
        else:
            logger.info("Native QR disabled — using raster fallback")
            self._write(self._graphics.qr_to_commands(value))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def print_diagnostics(self) -> None:
        self.initialize()
        self.text(f"MPU-L465 Python Driver v{_VERSION}\n")
        self.text(f"Transport: {self.transport}\n")
        self.text(f"Width: {self.config.dots_per_line} dots\n")
        self.text(f"Codepage: {self.config.native_codepage}\n")
        self.text("--- Raster test ---\n", fallback=TextFallbackMode.RASTER)
        self.text("ASCII native: OK\n")
        self.text("Lambda raster: λ\n")
        self.text("Gear raster: ⚙\n")
        self.feed(3)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write(self, data: bytes) -> None:
        logger.debug("Writing %d bytes", len(data))
        self.transport.write(data)
