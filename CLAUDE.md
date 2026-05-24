# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`mpul465` is a device-specific Python driver for the SII/Seiko MPU-L465 thermal printer on Linux. It is **not** a generic ESC/POS framework. The library handles native text printing, raster image/SVG printing, and automatic Unicode fallback (unsupported characters are rasterized rather than dropped or errored).

## Commands

```bash
# Install for development (editable + dev extras)
pip install -e ".[dev]"

# Install with SVG support
pip install -e ".[dev,svg]"

# Run all unit tests (no hardware required)
pytest

# Run a single test file
pytest tests/test_commands.py

# Run only hardware tests (requires printer on /dev/ttyUSB0)
pytest -m hardware

# Skip hardware tests explicitly
pytest -m "not hardware"

# Lint and format
ruff check src tests
ruff format src tests

# Type check
mypy src

# CLI usage
mpul465 print-text --port /dev/ttyUSB0 "Hello"
mpul465 print-image --port /dev/ttyUSB0 logo.png --width fit
mpul465 print-svg --port /dev/ttyUSB0 logo.svg --width fit
mpul465 self-test --port /dev/ttyUSB0
mpul465 print-text "Hello" --dump-bytes
```

## Architecture

The printer object is a façade. It must not know how to dither images, parse SVG, map Unicode to bytes, or pack raster rows — it delegates to specialized classes:

```
MPUL465Printer  (src/mpul465/printer.py)
  → Transport        writes bytes to the device
  → CommandEncoder   converts operations into raw ESC/POS bytes (always returns bytes, never writes)
  → TextEngine       decides native vs. raster per line, produces PrintSegment list
      → CodePage     tests/encodes characters for the configured code page
      → TextRasterizer → Pillow ImageDraw for raster fallback
          → FontRegistry  resolves fonts by style
  → GraphicsEngine   orchestrates image/SVG → printer bytes
      → Rasterizer   load → resize → dither/threshold → 1-bit
      → BitPacker    packs 1-bit rows MSB-first into MonoRaster
      → CommandEncoder.raster_image()
```

### Key data model

`MonoRaster` is the internal representation passed between the graphics layer and the command encoder. It is deliberately not a Pillow image so that `CommandEncoder` has no Pillow dependency.

```python
@dataclass(frozen=True, slots=True)
class MonoRaster:
    width: int; height: int; data: bytes; stride: int
```

`PrintSegment = NativeTextSegment | RasterTextSegment` is what `TextEngine.render_text()` produces. `MPUL465Printer` iterates segments and dispatches each to the encoder.

### Text fallback policy (v0.1)

- If **every** character in a line is encodable in the native codepage → emit native bytes.
- If **any** character is unsupported → rasterize the **whole line** (mixed native/raster causes baseline/spacing problems).
- `fallback="strict"` raises `UnsupportedCharacterError` instead.
- `fallback="raster"` always rasterizes.
- Run-level fallback ("ABC λ DEF" → native/raster/native segments) is a **future feature**, not v0.1.

### Alignment rule

- Native text: use printer alignment commands.
- Raster text and images: pad the raster canvas to full print width **before** encoding.

### Transport protocol

Transport is a `typing.Protocol` (structural subtyping), not an ABC. Any class implementing `write(data: bytes) -> int`, `flush() -> None`, `close() -> None` qualifies. `DryRunTransport` captures bytes in a buffer and is the primary test transport.

### Configuration

`MPUL465Config` is `@dataclass(frozen=True, slots=True)`. `dots_per_line=384` is a configurable default — **must be verified with a calibration print on the actual hardware** before trusting it.

## Documentation index

| Document | Contents |
|----------|----------|
| [README.md](README.md) | Overview, quick start, installation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full layer map, data flows, key types |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, adding commands/transports, code style |
| [docs/api-reference.md](docs/api-reference.md) | Public API: all `MPUL465Printer` methods |
| [docs/configuration.md](docs/configuration.md) | `MPUL465Config` fields, `UnicodePolicy`, `NativeFontMetrics` |
| [docs/transports.md](docs/transports.md) | `SerialTransport`, `FileTransport`, `DryRunTransport`, custom transports |
| [docs/text-and-unicode.md](docs/text-and-unicode.md) | `TextEngine`, `CodePage`, fallback modes, `TextRasterizer`, `FontRegistry` |
| [docs/graphics.md](docs/graphics.md) | Raster pipeline, `BitPacker`, `MonoRaster`, SVG pipeline, alignment |
| [docs/commands.md](docs/commands.md) | `CommandEncoder` methods, constants, golden byte tests |
| [docs/exceptions.md](docs/exceptions.md) | Exception hierarchy and attributes |
| [docs/testing.md](docs/testing.md) | Test patterns, fixtures, golden files, hardware tests |
| [docs/hardware.md](docs/hardware.md) | Calibration, baud rate, command verification table, known quirks |
| [docs/cli.md](docs/cli.md) | All CLI subcommands and options |
| [docs/roadmap.md](docs/roadmap.md) | Versioned feature plan, acceptance criteria per version |

## Versioned scope

| Version | What to build |
|---------|--------------|
| v0.1 | Serial/file/dry-run transport, initialize, feed, native text, bold, underline, align, basic raster image, diagnostic page |
| v0.2 | CodePage model, unsupported-char detection, whole-line raster fallback, font registry, raster text wrapping, all fallback modes |
| v0.3 | SVG support via optional CairoSVG dep |
| v0.4 | Native QR/barcode (verify empirically); raster fallback if native is unreliable |
| v0.5 | CLI polish |

## Dependencies

- **Required:** `pyserial>=3.5`, `Pillow>=10`
- **Optional svg:** `CairoSVG>=2.7`
- **Dev:** `pytest`, `ruff`, `mypy`

Do not bundle fonts. Prefer system fonts (DejaVu Sans, Noto Sans/Mono) for broad Unicode coverage.

## Testing conventions

- All unit tests run **without hardware**. Use `DryRunTransport`.
- Hardware tests are marked `@pytest.mark.hardware` and skipped by default.
- Golden byte files live in `tests/golden/` (e.g. `hello.bin`, `bold.bin`).
- Command encoding is deterministic — test bytes directly: `assert CommandEncoder().initialize() == b"\x1b@"`.
- Use `pytest`'s `tmp_path` fixture for image-generation tests.

## SVG security

Treat SVG as untrusted input. Do not fetch remote resources from SVG content. Prefer local-only rendering. Document any system-library (CairoSVG/libcairo) dependencies explicitly.

## Logging

Use `logging.getLogger(__name__)` throughout. Never `print()` from library code (only from `cli.py`).

| Level | When |
|-------|------|
| debug | byte lengths, raster dimensions |
| info | transport opened, job printed |
| warning | raster fallback triggered |
| error | transport failure, render failure |

## Threading

The printer object is synchronous and **not thread-safe** for v0.1. Document this; do not add a spooler.
