# mpul465

Python driver for the SII/Seiko MPU-L465 thermal printer on Linux.

## Current status

| Milestone | What's included | State |
|-----------|----------------|-------|
| **v0.1** — Hardware bring-up | Serial/file/USB/dry-run transports, `CommandEncoder`, `MPUL465Printer` façade, raster image pipeline, `BitPacker`, `GraphicsEngine`, CLI (`print-text`, `print-image`, `self-test`, `dump`), CI, 46 tests | **Complete** |
| **v0.2** — Unicode fallback | `UnicodePolicy` (NFC normalization, transliteration, replacement char), `TextEngine` with all four fallback modes, `TextRasterizer`, `FontRegistry`, raster and native text wrapping, 63 tests total | **Complete** |
| **v0.3** — SVG support | `VectorRenderer` (CairoSVG), `GraphicsEngine.svg_to_commands()`, `printer.svg()` | Stub — needs CairoSVG integration |
| **v0.4** — Barcodes and QR | Native QR and barcode commands | Not started — requires hardware verification |
| **v0.5** — CLI polish | Shell completion, consistent exit codes, first PyPI release | Not started |

Hardware-verified values (`dots_per_line`, native column count, QR/barcode command formats) are pending physical printer arrival.

## Features

- Native receipt-style text printing with ESC/POS commands
- Automatic Unicode fallback: characters outside the printer's native code page are rasterized rather than dropped or corrupted
- Raster image printing (PNG, JPEG, BMP, TIFF, Pillow `Image` objects)
- SVG vector input (optional dependency)
- Clean, class-based API for scripts, CLI tools, and application integration
- All unit tests run without hardware

## Installation

```bash
# Core (serial + raster images)
pip install mpul465

# With SVG support
pip install "mpul465[svg]"
```

## Quick start

```python
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

with MPUL465Printer(SerialTransport("/dev/ttyUSB0")) as printer:
    printer.initialize()
    printer.text("Hello from Python\n")
    printer.bold("Bold line\n")
    printer.feed(3)
```

## Unicode fallback

```python
printer.text("Temperature: 72°F\n")    # native if cp437 is active
printer.text("Lambda: λ\n")            # auto: rasterized, no error
printer.text("λ\n", fallback="strict") # raises UnsupportedCharacterError
printer.text("café\n", fallback="raster")  # always rasterize
```

## Images and SVG

```python
printer.image("logo.png", width="fit")
printer.image("logo.png", width=256)
printer.svg("logo.svg", width="fit")    # requires mpul465[svg]
```

## CLI

```bash
mpul465 print-text --port /dev/ttyUSB0 "Hello"
mpul465 print-image --port /dev/ttyUSB0 logo.png --width fit
mpul465 print-svg --port /dev/ttyUSB0 logo.svg --width fit
mpul465 self-test --port /dev/ttyUSB0
mpul465 print-text "Hello" --dump-bytes
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,svg]"
```

Run quality checks:

```bash
hatch run test       # pytest (no hardware)
hatch run lint       # ruff check + format check
hatch run typecheck  # mypy
hatch run check      # all three
```

## Requirements

- Python 3.11+
- Linux (primary target)
- `pyserial >= 3.5`
- `Pillow >= 10`
- Optional: `CairoSVG >= 2.7` for SVG support

## Hardware notes

The MPU-L465 is a discontinued SII printer. Some command behaviors must be verified empirically on the hardware before trusting them. See [docs/hardware.md](docs/hardware.md) for calibration steps and the command verification checklist.

## API stability

This project follows [Semantic Versioning](https://semver.org/). Pre-1.0 releases may include breaking API changes between minor versions. The public API surface is `MPUL465Printer`, `MPUL465Config`, the transport classes, and the exception hierarchy.

## License

See [LICENSE](LICENSE).
