# Graphics

## Overview

The graphics system converts raster images and SVG vector files into 1-bit thermal printer output. The pipeline is structured so each step is independently testable: Pillow operations in `Rasterizer`, bit packing in `BitPacker`, byte generation in `CommandEncoder`.

---

## GraphicsEngine

`GraphicsEngine` orchestrates the full pipeline from input to printer bytes.

```python
class GraphicsEngine:
    def __init__(
        self,
        rasterizer: Rasterizer,
        encoder: CommandEncoder,
        config: MPUL465Config,
    ) -> None: ...

    def image_to_commands(
        self,
        image: Image.Image,
        *,
        width: int | str | None = None,
    ) -> bytes: ...

    def svg_to_commands(
        self,
        svg: str | bytes | Path,
        *,
        width: int | str | None = None,
    ) -> bytes: ...
```

`MPUL465Printer.image()` and `.svg()` load the input and hand it to `GraphicsEngine`. The engine returns `bytes` ready to write to the transport.

---

## Raster image pipeline

```
input (path / bytes / PIL Image)
  ↓ PIL Image.open() or pass-through
  ↓ apply EXIF orientation (if JPEG)
  ↓ convert to grayscale (mode "L")
  ↓ resize to target width (preserve aspect ratio)
  ↓ threshold / dither to 1-bit (mode "1")
  ↓ BitPacker.pack_msb_first()  →  MonoRaster
  ↓ chunk into bands of config.image_chunk_height rows
  ↓ CommandEncoder.raster_image(band)  →  bytes per band
  ↓ concatenate all band bytes
```

### Width resolution

| `width` value | Result |
|---------------|--------|
| `None` | Natural image width; clipped at `config.dots_per_line` if wider |
| `"fit"` | Scale to `config.dots_per_line`, preserve aspect ratio |
| `int` | Scale to that exact pixel width, preserve aspect ratio |

### Dithering

Controlled by `config.image_dither`:

| Value | Effect |
|-------|--------|
| `"floyd-steinberg"` | Error-diffusion dithering; best for photographs and gradients |
| `"none"` | Simple threshold at 50% grey; best for line art and logos |

Pillow's `Image.convert("1")` applies Floyd-Steinberg dithering by default. Pass `dither=Image.Dither.NONE` for threshold-only conversion.

---

## Rasterizer

Handles the Pillow operations: open, orient, resize, convert to 1-bit.

```python
class Rasterizer:
    def prepare(
        self,
        image: Image.Image,
        *,
        target_width: int,
        dither: str = "floyd-steinberg",
    ) -> Image.Image: ...     # returns 1-bit PIL Image, ready for packing
```

Input images are not modified in place. `prepare()` returns a new image.

---

## BitPacker

Packs a 1-bit Pillow image into a `MonoRaster` byte array.

```python
class BitPacker:
    def pack_msb_first(
        self,
        image: Image.Image,
        *,
        black_bit: Literal[0, 1] = 1,
        bit_order: Literal["msb", "lsb"] = "msb",
    ) -> MonoRaster: ...
```

Default behavior matches the most common ESC/POS convention:

- Black pixel → `1`
- White pixel → `0`
- Leftmost pixel → high bit of byte (MSB-first)

Some printer commands invert this convention. `black_bit=0` and `bit_order="lsb"` are provided for those cases.

### Stride calculation

```
stride = ceil(width / 8)
```

For `width=384`: `stride = 48` bytes per row.

---

## MonoRaster

The internal 1-bit image representation. `CommandEncoder` accepts this; it has no Pillow dependency.

```python
@dataclass(frozen=True, slots=True)
class MonoRaster:
    width: int    # pixels
    height: int   # pixels
    data: bytes   # packed 1-bit rows, MSB-first by default
    stride: int   # bytes per row = ceil(width / 8)
```

Bands: `GraphicsEngine` slices `MonoRaster.data` into chunks of `config.image_chunk_height * stride` bytes and passes each chunk to `CommandEncoder.raster_image()`.

---

## SVG pipeline

```
SVG input (path / bytes / str)
  ↓ VectorRenderer.render(svg)  →  PNG bytes
  ↓ PIL Image.open(BytesIO(png_bytes))
  ↓ [same raster pipeline as above]
```

SVG support requires the `svg` optional dependency:

```bash
pip install "mpul465[svg]"
```

### VectorRenderer

```python
class VectorRenderer:
    def render(
        self,
        svg: str | bytes | Path,
        *,
        scale: float = 1.0,
    ) -> bytes: ...   # PNG bytes
```

Backed by CairoSVG. The render scale is set so the resulting PNG width is at least `config.dots_per_line` pixels before the raster pipeline resizes it.

### SVG security

Treat all SVG input as untrusted:

- Remote resource references (`<image href="http://...">`, external stylesheets) are not fetched. CairoSVG's `unsafe=False` default enforces this.
- Do not shell out to render SVG; use `cairosvg.svg2png()` directly.
- Document any system-library dependencies (libcairo, libpango) clearly in installation instructions.

If you receive an SVG from an untrusted source, consider validating or sanitizing it before passing it to the library.

### Vector support scope (v0.1)

Only SVG is supported. Do not attempt PDF, EPS, DXF, KiCAD, or other vector formats in v0.1 — those are future optional renderers.

---

## Chunking

Thermal printers often have a maximum raster band height. `image_chunk_height` (default 24) controls how many rows are sent per command. The printer processes bands sequentially.

If the image height is not a multiple of `image_chunk_height`, the last band is padded with white rows to make it a full band.

---

## Alignment of raster content

Raster images and raster-fallback text are aligned by padding the `MonoRaster` canvas to `config.dots_per_line` pixels wide **before** packing. The printer does not receive a separate alignment command for raster content. This produces consistent output regardless of the printer's current alignment register state.

For center alignment, the image is padded symmetrically on both sides. For right alignment, it is left-padded.
