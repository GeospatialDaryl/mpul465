# Configuration

## MPUL465Config

All device-specific parameters are collected in one immutable dataclass. Nothing else in the codebase should contain hard-coded printer dimensions.

```python
from mpul465 import MPUL465Config

config = MPUL465Config(
    dots_per_line=384,
    native_codepage="cp437",
)
printer = MPUL465Printer(transport, config=config)
```

`MPUL465Config` is `@dataclass(frozen=True, slots=True)`, so instances are immutable and memory-efficient.

---

## Fields

### Print geometry

| Field | Default | Description |
|-------|---------|-------------|
| `dots_per_line` | `384` | Printable width in pixels. **Must be verified on hardware.** See below. |
| `image_chunk_height` | `24` | Rows per raster band sent to the printer. |

`384` dots is a common 58 mm-class thermal print width, but the actual value for the MPU-L465 must be confirmed with a calibration print before relying on it. See [docs/hardware.md](hardware.md).

### Text and encoding

| Field | Default | Description |
|-------|---------|-------------|
| `default_encoding` | `"ascii"` | Conservative encoding for safe output. |
| `native_codepage` | `"cp437"` | Code page active in the printer. Used by `CodePage` to test and encode characters. |

If you change `native_codepage`, `CodePage` will use Python's `str.encode()` with that codec name. Confirm that the printer is actually configured for the same code page.

### Font

| Field | Default | Description |
|-------|---------|-------------|
| `default_font_path` | `None` | Path to the default TrueType/OpenType font for raster text rendering. `None` means the `FontRegistry` will search for a system font. |
| `default_font_size` | `24` | Font size in points for raster text fallback. |

### Feature flags

| Field | Default | Description |
|-------|---------|-------------|
| `enable_native_qr` | `True` | Use native printer QR command. Set `False` to force raster fallback. |
| `enable_native_barcode` | `True` | Use native printer barcode commands. Set `False` to force raster fallback. |

### Image processing

| Field | Default | Description |
|-------|---------|-------------|
| `image_dither` | `"floyd-steinberg"` | Dithering algorithm applied when converting images to 1-bit. Valid values: `"floyd-steinberg"`, `"none"`. |

---

## Example configurations

### Minimal (defaults)

```python
config = MPUL465Config()
```

### Conservative strict mode

```python
config = MPUL465Config(
    native_codepage="ascii",
    enable_native_qr=False,
    enable_native_barcode=False,
    image_dither="none",
)
```

### Custom font and width

```python
from pathlib import Path

config = MPUL465Config(
    dots_per_line=384,
    default_font_path=str(Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")),
    default_font_size=20,
)
```

### Verified hardware width

```python
# After running a calibration print and confirming dots_per_line
config = MPUL465Config(dots_per_line=384)  # update if calibration differs
```

---

## UnicodePolicy

Controls how Unicode normalization and transliteration are applied before encoding.

```python
from mpul465.text import UnicodePolicy

policy = UnicodePolicy(
    normalize="NFC",       # "none" | "NFC" | "NFKC"
    transliterate=False,   # True = é → e (opt-in, lossy)
    replacement="?",       # used in "native" fallback mode
)
```

Default is `normalize="NFC"`. Aggressive transliteration (`transliterate=True`) is opt-in because it is lossy — acceptable for receipts but potentially wrong for names, labels, or encoded data.

---

## NativeFontMetrics

Used by the text wrapping system to compute column counts for native printer fonts.

```python
@dataclass(frozen=True, slots=True)
class NativeFontMetrics:
    columns_normal: int
    columns_double_width: int
```

These values depend on the active printer font mode and must be verified on hardware. See [docs/hardware.md](hardware.md).
