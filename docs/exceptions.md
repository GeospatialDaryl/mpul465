# Exceptions

## Hierarchy

```
MPUL465Error
├── TransportError
├── PrinterNotReadyError
├── UnsupportedCharacterError
├── CommandNotSupportedError
└── GraphicsRenderError
    ├── SVGRenderError
    └── ImageTooWideError
```

All exceptions are importable from `mpul465.exceptions` or from the top-level `mpul465` package.

---

## MPUL465Error

Base class for all library exceptions. Catch this if you want to handle any library error without caring about the specific type.

```python
from mpul465.exceptions import MPUL465Error

try:
    printer.text("Hello\n")
except MPUL465Error as exc:
    logger.error("Printer error: %s", exc)
```

---

## TransportError

Raised when the transport fails to write, flush, or close. Wraps the underlying OS or pyserial error.

```python
from mpul465.exceptions import TransportError

try:
    printer.text("Hello\n")
except TransportError as exc:
    print(f"Transport failed: {exc}")
```

---

## PrinterNotReadyError

Raised when the printer is addressed before `initialize()` is called, or when the printer signals a not-ready state.

---

## UnsupportedCharacterError

Raised in `fallback="strict"` mode when the input string contains characters that cannot be encoded in the native code page.

```python
from mpul465.exceptions import UnsupportedCharacterError

try:
    printer.text("λ = wavelength\n", fallback="strict")
except UnsupportedCharacterError as exc:
    print(f"Cannot print natively: {exc.characters}")   # {'λ'}
    print(f"Fallback mode was: {exc.fallback}")
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `characters` | `set[str]` | Characters that failed encoding |
| `fallback` | `str` | The fallback mode that was active |

### Design rule

Exceptions must include enough context to debug without re-running the operation. `UnsupportedCharacterError` always carries the specific characters and the active mode.

---

## CommandNotSupportedError

Raised when a command is requested that is not supported by the hardware configuration or has not been verified on the target printer.

```python
from mpul465.exceptions import CommandNotSupportedError

# If native QR is disabled:
# config = MPUL465Config(enable_native_qr=False)
# printer.qr("...") → falls back to raster, no exception

# If the command is structurally unsupported:
try:
    printer.barcode("12345", BarcodeKind.PDF417)
except CommandNotSupportedError as exc:
    print(f"Barcode type not supported: {exc}")
```

---

## GraphicsRenderError

Base class for errors in the graphics pipeline.

### SVGRenderError

Raised when the SVG renderer (CairoSVG) fails to parse or render the input.

```python
from mpul465.exceptions import SVGRenderError

try:
    printer.svg("broken.svg", width="fit")
except SVGRenderError as exc:
    print(f"SVG failed: {exc}")
```

### ImageTooWideError

Raised when `width=None` and the image is wider than `config.dots_per_line` and clipping is not permitted by the operation.

```python
from mpul465.exceptions import ImageTooWideError

try:
    printer.image("wide.png")   # width=None, image is 800px wide, dots_per_line=384
except ImageTooWideError as exc:
    print(f"Image is {exc.image_width}px; printer width is {exc.print_width}px")
    print("Use width='fit' to scale it down")
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `image_width` | `int` | Actual image width in pixels |
| `print_width` | `int` | `config.dots_per_line` |

---

## Logging vs. exceptions

The library logs at `warning` level when raster fallback occurs (auto mode) and at `error` level for transport and render failures. Exceptions are raised for conditions the caller must handle. Auto-mode fallback is not an exception — it is the designed behavior.

See [docs/testing.md](testing.md) for how to test exception paths.
