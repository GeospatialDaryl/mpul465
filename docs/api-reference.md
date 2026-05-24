# API Reference

## MPUL465Printer

The primary user-facing façade. Orchestrates transport, command encoding, text, and graphics.

```python
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

printer = MPUL465Printer(SerialTransport("/dev/ttyUSB0"))
```

### Constructor

```python
MPUL465Printer(
    transport: Transport,
    config: MPUL465Config | None = None,
)
```

If `config` is omitted, `MPUL465Config()` defaults are used.

### Context manager

```python
with MPUL465Printer(transport) as printer:
    printer.initialize()
    printer.text("Hello\n")
```

`__exit__` calls `close()`.

---

### Lifecycle

#### `initialize() -> None`

Sends the printer initialization command (`ESC @`). Resets formatting to defaults. Call once at the start of a print job.

#### `reset() -> None`

Equivalent to `initialize()`. Provided as a semantic alias.

#### `flush() -> None`

Flushes the underlying transport buffer.

#### `close() -> None`

Closes the transport.

---

### Text

#### `text(value: str, *, fallback: str = "auto") -> None`

Prints a Unicode string. Applies the configured fallback policy to handle characters outside the native code page.

| `fallback` | Behavior |
|------------|----------|
| `"auto"` | Native if the whole line is encodable; rasterize the whole line otherwise |
| `"native"` | Encode natively; apply replacement policy for unsupported characters |
| `"raster"` | Always rasterize, even if native encoding would succeed |
| `"strict"` | Raise `UnsupportedCharacterError` if any character is unsupported |

```python
printer.text("Hello\n")
printer.text("λ = wavelength\n")                 # auto: rasterized
printer.text("λ\n", fallback="strict")           # raises UnsupportedCharacterError
printer.text("café\n", fallback="raster")        # always raster
```

#### `line(value: str = "") -> None`

Prints `value + "\n"`. Convenience wrapper around `text`.

#### `bold(value: str) -> None`

Enables bold, prints `value`, then disables bold.

#### `underline(value: str) -> None`

Enables underline, prints `value`, then disables underline.

---

### Layout

#### `align(mode: Alignment) -> None`

Sets horizontal alignment for subsequent content.

```python
from mpul465 import Alignment

printer.align(Alignment.CENTER)
printer.text("Centered\n")
printer.align(Alignment.LEFT)
```

Valid values: `Alignment.LEFT`, `Alignment.CENTER`, `Alignment.RIGHT`.

Note: For raster content (images, raster-fallback text), alignment is achieved by padding the raster canvas to full print width before encoding, not by sending an alignment command.

#### `feed(lines: int = 1) -> None`

Advances paper by `lines` lines. `lines` must be in `[0, 255]`.

---

### Images and graphics

#### `image(image: str | Path | Image.Image, *, width: int | str | None = None) -> None`

Prints a raster image.

| `width` | Behavior |
|---------|----------|
| `None` | Natural image width; clipped if wider than print width |
| `"fit"` | Scale to `config.dots_per_line`, preserving aspect ratio |
| `int` | Scale to exact pixel width, preserving aspect ratio |

```python
printer.image("logo.png", width="fit")
printer.image("logo.png", width=256)
printer.image(pil_image, width="fit")
```

Supported input formats: PNG, JPEG, BMP, TIFF, and any `PIL.Image.Image`.

#### `svg(svg: str | bytes | Path, *, width: int | str | None = None) -> None`

Prints an SVG file. Requires the `svg` optional dependency (`pip install "mpul465[svg]"`).

The `width` parameter behaves identically to `image()`.

```python
printer.svg("logo.svg", width="fit")
printer.svg(svg_bytes, width=300)
```

Treat SVG source as untrusted. Remote resource references in SVG are not fetched.

---

### Barcodes

#### `barcode(value: str, kind: BarcodeKind) -> None`

Prints a 1D barcode using a native printer barcode command (if supported by the hardware). Falls back to raster if `config.enable_native_barcode` is `False`.

#### `qr(value: str) -> None`

Prints a QR code using native printer QR commands (if supported). Falls back to raster if `config.enable_native_qr` is `False`.

---

### Diagnostics

#### `print_diagnostics() -> None`

Prints a self-test page showing library version, transport, configured width, code page, a black/white raster pattern, Unicode fallback samples, and a QR code. Use this for hardware bring-up and verification.

---

## Alignment

```python
from mpul465 import Alignment

class Alignment(StrEnum):
    LEFT   = "left"
    CENTER = "center"
    RIGHT  = "right"
```

---

## TextFallbackMode

```python
from mpul465 import TextFallbackMode

class TextFallbackMode(StrEnum):
    AUTO   = "auto"
    NATIVE = "native"
    RASTER = "raster"
    STRICT = "strict"
```

---

## BarcodeKind

Defined in `mpul465.constants`. Exact members depend on which barcode types are confirmed supported by the hardware. See [docs/hardware.md](hardware.md).

---

## Exceptions

See [docs/exceptions.md](exceptions.md) for the full exception hierarchy and usage examples.
