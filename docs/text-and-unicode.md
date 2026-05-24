# Text and Unicode

## Overview

The text system is the most complex part of the library because it must transparently handle the boundary between characters the printer understands natively and characters that require raster fallback. The goal is that **no character is silently dropped or corrupted** — if the printer cannot print a glyph natively, the library rasterizes it.

---

## TextEngine

`TextEngine` is the decision layer between `MPUL465Printer.text()` and the transport. It accepts a Python `str` and returns a list of `PrintSegment` objects that `MPUL465Printer` dispatches to the encoder.

```python
class TextEngine:
    def __init__(
        self,
        codepage: CodePage,
        rasterizer: TextRasterizer,
        config: MPUL465Config,
    ) -> None: ...

    def render_text(self, text: str, *, fallback: str = "auto") -> list[PrintSegment]: ...
```

`MPUL465Printer` holds a `TextEngine` instance and calls `render_text()` inside `text()`. The printer should not contain any character-encoding logic itself.

---

## PrintSegment

The output of `TextEngine.render_text()` is a list of segments:

```python
@dataclass(frozen=True, slots=True)
class NativeTextSegment:
    data: bytes          # ready to send to the printer

@dataclass(frozen=True, slots=True)
class RasterTextSegment:
    image: MonoRaster    # ready to pass to CommandEncoder.raster_image()

PrintSegment = NativeTextSegment | RasterTextSegment
```

`MPUL465Printer` iterates the list and dispatches each segment:

```python
for segment in self.text_engine.render_text(value, fallback=fallback):
    match segment:
        case NativeTextSegment(data=data):
            self.write(self.commands.text_bytes(data))
        case RasterTextSegment(image=image):
            self.write(self.commands.raster_image(image))
```

---

## Fallback modes

Controlled by the `fallback` parameter on `printer.text()` or `TextFallbackMode`:

| Mode | Behavior |
|------|----------|
| `"auto"` | Native if every character in the line is encodable; rasterize the whole line otherwise |
| `"native"` | Encode natively; replace unsupported characters per `UnicodePolicy.replacement` |
| `"raster"` | Always rasterize the line, even if native encoding would succeed |
| `"strict"` | Raise `UnsupportedCharacterError` if any character is unsupported |

### v0.1 policy: whole-line rasterization

In v0.1, the unit of raster fallback is the **whole line**, not the individual character or run. If a single unsupported character appears, the entire line is rasterized.

This is intentional. Mixed native/raster output on the same line causes baseline misalignment, inconsistent line spacing, and unpredictable column width behaviour. Whole-line rasterization avoids all of these problems at the cost of some printer-native characters also going through the raster path.

Run-level fallback (e.g. `"ABC "` native + `"λ"` raster + `" DEF"` native) is a future feature. It requires solving raster glyph baseline alignment against native printer glyphs, which is a separate problem.

---

## CodePage

`CodePage` encapsulates character-set testing and encoding for the configured native code page.

```python
class CodePage:
    name: str                                   # e.g. "cp437"

    def can_encode(self, text: str) -> bool: ...        # True if all chars encodable
    def encode(self, text: str) -> bytes: ...           # raises on failure
    def unsupported_chars(self, text: str) -> set[str]: ...
```

Implementation uses Python's built-in codec system. `can_encode("λ")` under `cp437` will return `False` because `"λ".encode("cp437")` raises `UnicodeEncodeError`.

---

## UnicodePolicy

Controls normalization and transliteration applied before encoding tests.

```python
@dataclass(frozen=True, slots=True)
class UnicodePolicy:
    normalize: Literal["none", "NFC", "NFKC"] = "NFC"
    transliterate: bool = False
    replacement: str = "?"
```

- `normalize="NFC"` is the default. NFC composes combining characters, so `"é"` (e + combining acute) becomes `"é"` before the encoding test.
- `normalize="NFKC"` additionally maps compatibility characters (e.g. `"ﬁ"` → `"fi"`). More aggressive.
- `transliterate=True` maps accented characters to ASCII equivalents (`"é"` → `"e"`). This is **opt-in and lossy**. Acceptable for simple receipts; potentially wrong for names, labels, or encoded data.
- `replacement` is used in `"native"` fallback mode when a character cannot be encoded.

---

## TextRasterizer

Converts a text string to a `MonoRaster` using Pillow's `ImageDraw` and `ImageFont`.

```python
class TextRasterizer:
    def __init__(
        self,
        font_registry: FontRegistry,
        config: MPUL465Config,
    ) -> None: ...

    def render_line(
        self,
        text: str,
        *,
        width: int,
        align: Alignment = Alignment.LEFT,
        font_size: int | None = None,
    ) -> MonoRaster: ...
```

The canvas is padded to `width` pixels before being converted to `MonoRaster`, so alignment is baked into the raster data rather than relying on a printer alignment command.

### Font measurement

Raster text wrapping uses Pillow's text measurement APIs (`ImageDraw.textbbox` or `ImageFont.getbbox`), not character count. This correctly handles proportional fonts and Unicode characters of varying widths.

---

## FontRegistry

Resolves a `PIL.ImageFont.FreeTypeFont` for a given `TextStyle`.

```python
class FontRegistry:
    def __init__(self, default_font: Path | None = None) -> None: ...
    def resolve(self, style: TextStyle) -> ImageFont.FreeTypeFont: ...
```

If `default_font` is `None`, the registry searches for a suitable system font in priority order:

1. DejaVu Sans (broad Latin/Greek/Cyrillic coverage)
2. Noto Sans (extensive Unicode coverage)
3. Noto Sans Mono
4. Any monospaced TrueType font found via `fc-list`

**Font files are not bundled with the library.** Install a system font package if the default search fails:

```bash
# Debian/Ubuntu
sudo apt install fonts-dejavu fonts-noto
```

---

## Text wrapping

### Native text wrapping

Native text wrapping is column-based and depends on `NativeFontMetrics`:

```python
@dataclass(frozen=True, slots=True)
class NativeFontMetrics:
    columns_normal: int
    columns_double_width: int
```

These values are hardware-dependent and must be verified empirically. See [docs/hardware.md](hardware.md).

### Raster text wrapping

```python
printer.text(long_text, wrap=True)
```

When `wrap=True`, `TextEngine` performs pixel-aware wrapping:

1. Split input into paragraphs at `\n`.
2. Measure text width with `ImageFont`.
3. Wrap at word boundaries such that no line exceeds `config.dots_per_line` pixels.
4. Rasterize each wrapped line independently.

---

## Complex script support

### Supported in MVP

- ASCII and standard Latin characters
- Common symbols and punctuation
- Greek letters
- Mathematical symbols (if the configured font supports them)
- Emoji rendered as monochrome glyphs (visual quality depends on font)

### Not supported in v0.1

The following require a libraqm integration for correct shaping and bidi:

- Arabic
- Hebrew mixed with Latin
- Devanagari and other Indic scripts
- Tibetan
- Complex combining mark sequences

Pillow documents libraqm as providing bidirectional text, shaping via HarfBuzz, and proper script itemization. Future versions may expose a `complex_text=True` mode that enables libraqm if installed.

---

## Example: observing unsupported characters

```python
from mpul465.exceptions import UnsupportedCharacterError

try:
    printer.text("λ = wavelength\n", fallback="strict")
except UnsupportedCharacterError as exc:
    print(f"Unsupported: {exc.characters}")   # {'λ'}
```

The `characters` attribute contains the set of characters that failed encoding.
