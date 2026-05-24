from __future__ import annotations

import logging
import math
from pathlib import Path

from PIL import Image

from mpul465.commands import CommandEncoder
from mpul465.config import MPUL465Config
from mpul465.exceptions import ImageTooWideError, SVGRenderError
from mpul465.graphics.packing import BitPacker
from mpul465.graphics.raster import Rasterizer

logger = logging.getLogger(__name__)


class GraphicsEngine:
    """Orchestrates image/SVG → printer bytes."""

    def __init__(
        self,
        rasterizer: Rasterizer,
        encoder: CommandEncoder,
        config: MPUL465Config,
    ) -> None:
        self._rasterizer = rasterizer
        self._encoder = encoder
        self._config = config
        self._packer = BitPacker()

    def image_to_commands(
        self,
        image: Image.Image,
        *,
        width: int | str | None = None,
    ) -> bytes:
        target = self._resolve_width(image.width, width)
        prepared = self._rasterizer.prepare(
            image,
            target_width=target,
            dither=self._config.image_dither,
        )
        return self._encode_bands(prepared)

    def svg_to_commands(
        self,
        svg: str | bytes | Path,
        *,
        width: int | str | None = None,
    ) -> bytes:
        try:
            import cairosvg  # type: ignore[import-untyped]
        except ImportError as exc:
            raise SVGRenderError(
                "SVG support requires 'mpul465[svg]': pip install 'mpul465[svg]'"
            ) from exc

        svg_bytes: bytes
        if isinstance(svg, Path):
            svg_bytes = svg.read_bytes()
        elif isinstance(svg, str):
            svg_bytes = Path(svg).read_bytes()
        else:
            svg_bytes = svg

        try:
            png_bytes: bytes = cairosvg.svg2png(
                bytestring=svg_bytes,
                unsafe=False,
                output_width=self._config.dots_per_line,
            )
        except Exception as exc:
            raise SVGRenderError(f"CairoSVG render failed: {exc}") from exc

        import io

        image = Image.open(io.BytesIO(png_bytes))
        return self.image_to_commands(image, width=width)

    def _resolve_width(self, natural_width: int, width: int | str | None) -> int:
        dots = self._config.dots_per_line
        if width is None:
            if natural_width > dots:
                raise ImageTooWideError(
                    f"Image width {natural_width}px exceeds dots_per_line={dots}. "
                    "Use width='fit' to scale.",
                    image_width=natural_width,
                    print_width=dots,
                )
            return natural_width
        if width == "fit":
            return dots
        if isinstance(width, int):
            return width
        raise ValueError(f"Invalid width value: {width!r}")

    def _encode_bands(self, image: Image.Image) -> bytes:
        raster = self._packer.pack_msb_first(image)
        chunk_h = self._config.image_chunk_height
        out = bytearray()
        for row in range(0, raster.height, chunk_h):
            band_h = min(chunk_h, raster.height - row)
            band_data = raster.data[row * raster.stride : (row + band_h) * raster.stride]
            from mpul465.models import MonoRaster

            band = MonoRaster(
                width=raster.width,
                height=band_h,
                data=band_data,
                stride=raster.stride,
            )
            out.extend(self._encoder.raster_image(band))
        return bytes(out)
