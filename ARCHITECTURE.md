# Architecture

## Design principle

`mpul465` is a device-specific driver, not a generic ESC/POS framework. The public surface (`MPUL465Printer`) is a thin façade. Every non-trivial concern lives in a specialized class that can be tested independently of the printer.

The critical rule: **`CommandEncoder` returns bytes. It never writes to anything.** This makes command encoding purely functional and trivially testable.

## Layer map

```
┌─────────────────────────────────────────────────────┐
│                  MPUL465Printer                      │  ← user-facing façade
│               src/mpul465/printer.py                 │
└───────┬─────────────────┬────────────────────────────┘
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────────────────────────┐
│   Transport   │  │         CommandEncoder            │
│ (Protocol)    │  │      src/mpul465/commands.py      │
│               │  │  returns bytes, never writes      │
└───────────────┘  └──────────────┬───────────────────┘
 SerialTransport                  │ uses
 FileTransport                    ▼
 UsbRawTransport    ┌─────────────────────────────────┐
 DryRunTransport    │           MonoRaster             │
                    │        src/mpul465/models.py     │
                    │  width, height, data, stride     │
                    └──────────────────────────────────┘
                              ▲               ▲
                              │               │
        ┌─────────────────────┘               └─────────────────────┐
        │                                                           │
┌───────────────────┐                                 ┌────────────────────────┐
│    TextEngine     │                                 │    GraphicsEngine      │
│ src/mpul465/      │                                 │  src/mpul465/          │
│   text/engine.py  │                                 │    graphics/__init__.py│
└───────┬───────────┘                                 └────────┬───────────────┘
        │                                                      │
   ┌────┴─────────────┐                              ┌─────────┴──────────────┐
   │                  │                              │                        │
   ▼                  ▼                              ▼                        ▼
┌────────┐   ┌────────────────┐             ┌──────────────┐     ┌──────────────────┐
│CodePage│   │TextRasterizer  │             │  Rasterizer  │     │   BitPacker      │
│        │   │  → FontRegistry│             │  (raster.py) │     │  (packing.py)    │
│codepages   │  → Pillow      │             │  Pillow ops  │     │  pack_msb_first  │
└────────┘   └────────────────┘             └──────────────┘     └──────────────────┘
                                                    ▲
                                                    │
                                            ┌───────────────┐
                                            │ VectorRenderer│
                                            │ (vector.py)   │
                                            │ CairoSVG      │
                                            └───────────────┘
```

## Data flow: printing text

```
printer.text("Café: λ\n")
  │
  ▼
TextEngine.render_text("Café: λ\n")
  │
  ├─ CodePage.can_encode("Café: λ\n")  →  False  (λ not in cp437)
  │
  ├─ fallback="auto"  →  rasterize whole line
  │
  ▼
TextRasterizer.render_line("Café: λ\n", width=384)
  │  Pillow ImageDraw + FreeTypeFont
  ▼
MonoRaster(width=384, height=32, data=..., stride=48)
  │
  ▼
RasterTextSegment(image=MonoRaster(...))
  │
  ▼  (back in MPUL465Printer)
CommandEncoder.raster_image(MonoRaster)  →  bytes
  │
  ▼
Transport.write(bytes)
```

## Data flow: printing an image

```
printer.image("logo.png", width="fit")
  │
  ▼
GraphicsEngine.image_to_commands(Image.open("logo.png"), width="fit")
  │
  ├─ apply EXIF orientation
  ├─ convert to grayscale
  ├─ resize to dots_per_line=384
  ├─ dither to 1-bit (Floyd-Steinberg default)
  │
  ▼
BitPacker.pack_msb_first(image)
  │
  ▼
MonoRaster(width=384, ...)
  │
  ├─ chunk into bands of image_chunk_height rows
  │
  ▼
CommandEncoder.raster_image(band)  →  bytes  (per band)
  │
  ▼
Transport.write(bytes)
```

## Data flow: printing SVG

```
printer.svg("logo.svg", width="fit")
  │
  ▼
GraphicsEngine.svg_to_commands(svg_bytes, width="fit")
  │
  ├─ VectorRenderer.render(svg_bytes)  →  PNG bytes  (CairoSVG)
  │
  ▼
  [same raster pipeline as image above]
```

## Key types

| Type | Module | Role |
|------|--------|------|
| `MPUL465Config` | `config.py` | Immutable device parameters |
| `Transport` | `transports/base.py` | Protocol; structural subtyping |
| `CommandEncoder` | `commands.py` | Pure byte generation |
| `MonoRaster` | `models.py` | Internal 1-bit image; boundary between graphics and encoder |
| `PrintSegment` | `models.py` | `NativeTextSegment \| RasterTextSegment` |
| `TextEngine` | `text/engine.py` | Native vs. raster decision, produces `PrintSegment` list |
| `CodePage` | `text/codepages.py` | Tests/encodes characters for a given code page |
| `TextRasterizer` | `text/engine.py` | Pillow-based text → `MonoRaster` |
| `FontRegistry` | `text/fonts.py` | Resolves fonts by style |
| `GraphicsEngine` | `graphics/__init__.py` | Orchestrates image/SVG → bytes |
| `Rasterizer` | `graphics/raster.py` | Pillow load/resize/dither |
| `BitPacker` | `graphics/packing.py` | Packs 1-bit rows; configurable polarity and bit order |
| `VectorRenderer` | `graphics/vector.py` | SVG → PNG via CairoSVG |

## What MPUL465Printer must NOT do

The façade must not contain:

- Dithering logic
- SVG parsing
- Unicode-to-byte mapping
- Bit packing
- Serial port management

If you find yourself writing any of these in `printer.py`, move the logic to the appropriate module.

## Configuration

`MPUL465Config` is `@dataclass(frozen=True, slots=True)`. All device-specific constants live here. Nothing else in the codebase should have hard-coded printer dimensions.

`dots_per_line=384` is a configurable default that **must be verified on the actual hardware** via a calibration print before trusting it. See [docs/hardware.md](docs/hardware.md).

## Threading

The printer object is synchronous and not thread-safe in v0.1. One instance represents one active connection to one printer. External locking is required if shared across threads. A `PrinterSpooler` is a future option; do not add it now.
