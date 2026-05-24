# Command Encoding

## Overview

`CommandEncoder` is the only place in the library that knows the ESC/POS byte sequences sent to the printer. Every method returns `bytes`. No method writes to any transport or has side effects.

This design makes command encoding purely functional and trivially testable without hardware:

```python
def test_initialize() -> None:
    assert CommandEncoder().initialize() == b"\x1b@"

def test_feed_3_lines() -> None:
    assert CommandEncoder().feed_lines(3) == b"\x1bd\x03"
```

---

## Constants

```python
ESC = b"\x1b"
GS  = b"\x1d"
LF  = b"\x0a"
```

These are defined as module-level constants in `src/mpul465/constants.py`. Command methods use the symbolic constants rather than raw bytes so the intent is always readable.

---

## CommandEncoder methods

### Lifecycle

| Method | Returns | ESC/POS command |
|--------|---------|-----------------|
| `initialize()` | `bytes` | `ESC @` — printer reset |

### Paper feed

| Method | Returns | Notes |
|--------|---------|-------|
| `line_feed()` | `bytes` | `LF` |
| `feed_lines(lines: int)` | `bytes` | `ESC d n`; `lines` must be in `[0, 255]` |

### Text formatting

| Method | Returns | Notes |
|--------|---------|-------|
| `bold(enabled: bool)` | `bytes` | `ESC E 1` / `ESC E 0` |
| `underline(enabled: bool)` | `bytes` | `ESC - 1` / `ESC - 0` |
| `align(mode: Alignment)` | `bytes` | `ESC a n`; 0=left, 1=center, 2=right |

### Text data

| Method | Returns | Notes |
|--------|---------|-------|
| `text_bytes(data: bytes)` | `bytes` | Pass-through; validates and returns the bytes |

### Raster graphics

| Method | Returns | Notes |
|--------|---------|-------|
| `raster_image(image: MonoRaster)` | `bytes` | ESC/POS raster bitmap command; encodes one band |

The raster command format must be verified on the actual hardware. The expected form is `GS v 0` (raster transfer) or an equivalent, with width and height parameters prepended before the pixel data.

### Barcodes and QR

| Method | Returns | Notes |
|--------|---------|-------|
| `barcode(value: str, kind: BarcodeKind)` | `bytes` | Native barcode command if supported |
| `qr(value: str)` | `bytes` | Native QR command if supported |

These commands must be verified empirically. See [docs/hardware.md](hardware.md).

---

## Adding new commands

1. Add the method to `CommandEncoder`. It must return `bytes`.
2. Add a constant to `constants.py` if a new ESC/POS prefix is needed.
3. Write a unit test that asserts the exact byte output.
4. If the command's behavior is uncertain (many MPU-L465 commands are undocumented), add a note in [docs/hardware.md](hardware.md) and mark the test `@pytest.mark.hardware` for empirical verification.

---

## Golden byte tests

Expected byte output for common operations is stored in `tests/golden/`:

```
tests/golden/
  hello.bin
  bold.bin
  feed_3.bin
  small_bitmap.bin
```

Golden files are committed binary files. When a command encoding changes deliberately, regenerate the golden file and commit it with the change. Tests that read golden files:

```python
from pathlib import Path

def test_hello_golden() -> None:
    expected = (Path(__file__).parent / "golden" / "hello.bin").read_bytes()
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.text("Hello\n")
    assert transport.buffer == expected
```

---

## Unverified commands

The MPU-L465 technical reference is separate from the user guide and some command behaviors must be confirmed empirically. Commands in the following categories should be treated as tentative until verified on hardware:

- QR code native command format
- 1D barcode type parameter values
- Raster image transfer command variant (`GS v 0` vs. `ESC *`)
- Maximum raster band height
- Character code page selection command

Verified values should be documented in [docs/hardware.md](hardware.md) and hardened into unit tests.
