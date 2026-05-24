# Roadmap

## Version overview

| Version | Theme | Status |
|---------|-------|--------|
| v0.1 | Hardware bring-up | Complete |
| v0.2 | Unicode fallback | Complete |
| v0.3 | SVG support | Stub |
| v0.4 | Barcodes and QR | Not started |
| v0.5 | CLI polish | Stub |

---

## Implementation status

| Component | Source file | Test file | Status |
|-----------|-------------|-----------|--------|
| `MPUL465Config` | `src/mpul465/config.py` | — | Implemented |
| `MPUL465Printer` | `src/mpul465/printer.py` | `tests/test_printer_facade.py` | Implemented |
| `CommandEncoder` | `src/mpul465/commands.py` | `tests/test_commands.py` | Implemented (QR/barcode stubs) |
| `MonoRaster` / `PrintSegment` | `src/mpul465/models.py` | — | Implemented |
| `Transport` (Protocol) | `src/mpul465/transports/base.py` | — | Implemented |
| `SerialTransport` | `src/mpul465/transports/serial.py` | hardware only | Implemented |
| `FileTransport` | `src/mpul465/transports/file.py` | — | Implemented |
| `UsbRawTransport` | `src/mpul465/transports/usb_raw.py` | — | Implemented |
| `DryRunTransport` | `src/mpul465/transports/dry_run.py` | (used in all tests) | Implemented |
| `CodePage` | `src/mpul465/text/codepages.py` | `tests/test_codepages.py` | Implemented |
| `TextEngine` | `src/mpul465/text/engine.py` | `tests/test_text_engine.py` | Implemented |
| `TextRasterizer` | `src/mpul465/text/engine.py` | `tests/test_text_engine.py` | Implemented |
| `FontRegistry` | `src/mpul465/text/fonts.py` | — | Implemented |
| `NativeFontMetrics` / wrapping | `src/mpul465/text/wrapping.py` | — | Implemented |
| `GraphicsEngine` | `src/mpul465/graphics/__init__.py` | `tests/test_raster.py` | Implemented |
| `Rasterizer` | `src/mpul465/graphics/raster.py` | `tests/test_raster.py` | Implemented |
| `BitPacker` | `src/mpul465/graphics/packing.py` | `tests/test_packing.py` | Implemented |
| `VectorRenderer` | `src/mpul465/graphics/vector.py` | — | Stub (needs CairoSVG) |
| `CommandEncoder.qr()` | `src/mpul465/commands.py` | hardware only | Stub (verify on hardware) |
| `CommandEncoder.barcode()` | `src/mpul465/commands.py` | hardware only | Stub (verify on hardware) |
| `cli.py` | `src/mpul465/cli.py` | — | Implemented |
| `diagnostics.py` | `src/mpul465/diagnostics.py` | — | Implemented |
| Exception hierarchy | `src/mpul465/exceptions.py` | (used in test_text_engine, test_raster) | Implemented |
| Golden byte tests | `tests/golden/` | `tests/test_commands.py` | Not yet generated |
| CI workflow | `.github/workflows/ci.yml` | — | Implemented |

---

## v0.1 — Hardware bring-up

The goal of v0.1 is a working, minimal driver that can send bytes to the physical printer.

### Features

- `SerialTransport`, `FileTransport`, `DryRunTransport`
- `CommandEncoder` with: initialize, feed, bold, underline, align, text bytes, basic raster image
- `MPUL465Printer` façade with: `initialize()`, `text()` (ASCII only), `bold()`, `underline()`, `align()`, `feed()`, `image()`, `close()`
- `MPUL465Config` dataclass
- `print_diagnostics()` — diagnostic print page
- Basic `GraphicsEngine`: load → grayscale → resize → 1-bit → pack → chunk → encode
- `BitPacker.pack_msb_first()`
- `MonoRaster` model
- Exception hierarchy
- CLI: `print-text`, `print-image`, `self-test`, `dump`
- Unit tests for all command encoder methods
- Golden byte tests for common operations
- Hardware verification of print width, baud rate, and core commands

### Acceptance criteria

```python
with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.text("Plain ASCII receipt\n")
    printer.image("logo.png", width="fit")
    printer.feed(3)
```

- Unit tests pass without hardware
- Command bytes are deterministic
- Raster output dimensions are predictable

---

## v0.2 — Unicode fallback

### Features

- `CodePage` with `can_encode()`, `encode()`, `unsupported_chars()`
- `TextFallbackMode` enum
- `UnicodePolicy` with `normalize`, `transliterate`, `replacement`
- `TextEngine.render_text()` producing `PrintSegment` lists
- `NativeTextSegment` and `RasterTextSegment`
- `TextRasterizer` using Pillow `ImageDraw` + `ImageFont`
- `FontRegistry` with system font discovery
- Raster text wrapping by pixel width
- Native text wrapping by `NativeFontMetrics.columns_normal`
- All four fallback modes: `auto`, `native`, `raster`, `strict`
- `UnsupportedCharacterError` with `characters` attribute
- Logging at `warning` level for auto-mode raster fallback
- Unicode normalization (NFC default)

### Acceptance criteria

```python
printer.text("Temperature: 72°F\n")   # native or raster per code page
printer.text("Lambda: λ\n")           # raster fallback, no error
printer.text("λ\n", fallback="strict")  # raises UnsupportedCharacterError
```

- No character is ever silently dropped
- Unicode fallback tests pass without hardware
- Auto-mode fallback is logged at `warning` level

### Not in v0.2

Run-level fallback (mixing native and raster within one line). This requires solving baseline alignment between raster glyphs and native printer glyphs and is deferred.

---

## v0.3 — SVG support

### Features

- `VectorRenderer` backed by CairoSVG
- `GraphicsEngine.svg_to_commands()`
- `MPUL465Printer.svg()`
- `SVGRenderError` exception
- `svg` optional dependency group (`cairosvg>=2.7`)
- CLI: `print-svg` subcommand
- SVG security: no remote resource fetch, local-only rendering
- Documentation of system library requirements (libcairo)

### Acceptance criteria

```python
printer.svg("logo.svg", width="fit")
```

- Works without hardware (verify PNG rendering in tests)
- Clear error if `svg` optional dependency is not installed

### Not in v0.3

PDF, EPS, DXF, or other vector formats.

---

## v0.4 — Barcodes and QR

### Features

- Empirical verification of native QR command format on hardware
- Empirical verification of native 1D barcode command and supported types
- `CommandEncoder.qr()` and `CommandEncoder.barcode()`
- `BarcodeKind` enum populated with confirmed supported types
- Raster fallback for QR if native QR is unreliable
- `enable_native_qr` and `enable_native_barcode` config flags

### Acceptance criteria

```python
printer.qr("https://example.com")
printer.barcode("12345678", BarcodeKind.CODE128)
```

Hardware verification results documented in [docs/hardware.md](hardware.md).

---

## v0.5 — CLI polish

### Features

- All CLI subcommands complete and documented
- `--dump-bytes` flag on all print commands
- `--baudrate` global flag
- Consistent exit codes
- `--help` text for all commands
- Shell completion (optional: via `argcomplete` or `click`)
- First public release preparation: README, LICENSE, PyPI packaging

---

## Future (post v0.5)

These are acknowledged future possibilities, not planned work:

- **Run-level Unicode fallback**: mix native and raster segments within one line. Requires solving baseline alignment.
- **`PrinterSpooler`**: thread-safe queue-based spooler for shared printer access.
- **Complex text mode**: libraqm integration for Arabic, Hebrew, Indic scripts.
- **Additional vector renderers**: PDF, EPS (via poppler or Ghostscript).
- **Additional transports**: Bluetooth serial, network socket.
- **Async transport**: `asyncio`-compatible transport protocol.

Do not design for these in the current implementation. Three similar lines of code is better than a premature abstraction.
