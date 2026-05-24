from __future__ import annotations

from pathlib import Path

from mpul465.exceptions import SVGRenderError


class VectorRenderer:
    """Renders SVG to PNG bytes using CairoSVG.

    Requires the 'svg' optional dependency: pip install 'mpul465[svg]'.
    SVG is treated as untrusted: remote resource references are not fetched.
    """

    def render(
        self,
        svg: str | bytes | Path,
        *,
        output_width: int | None = None,
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
            return cairosvg.svg2png(  # type: ignore[no-any-return]
                bytestring=svg_bytes,
                unsafe=False,
                output_width=output_width,
            )
        except Exception as exc:
            raise SVGRenderError(f"CairoSVG render failed: {exc}") from exc
