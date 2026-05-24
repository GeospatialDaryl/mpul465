# Testing

## Philosophy

All unit tests run without hardware. Hardware is only required for `@pytest.mark.hardware` tests. This means CI can run the full non-hardware suite without a printer attached.

`DryRunTransport` is the workhorse for unit tests. It captures all bytes written by the printer object so assertions can compare exact byte output.

---

## Running tests

```bash
# All unit tests (no hardware required)
pytest

# Single file
pytest tests/test_commands.py

# Single test
pytest tests/test_commands.py::test_initialize_command

# With verbose output
pytest -v

# Hardware tests only (requires printer on /dev/ttyUSB0)
pytest -m hardware

# All tests except hardware
pytest -m "not hardware"

# Show print statements (useful when debugging raster output)
pytest -s
```

---

## Test structure

```
tests/
  conftest.py              # shared fixtures
  test_commands.py         # CommandEncoder byte output
  test_codepages.py        # CodePage encoding tests
  test_text_engine.py      # TextEngine native/raster decisions
  test_raster.py           # Rasterizer and image pipeline
  test_packing.py          # BitPacker
  test_printer_facade.py   # MPUL465Printer integration (DryRunTransport)
  golden/
    hello.bin
    bold.bin
    feed_3.bin
    small_bitmap.bin
```

---

## Command encoding tests

Test exact byte output. No transport, no printer.

```python
def test_initialize_command() -> None:
    assert CommandEncoder().initialize() == b"\x1b@"

def test_bold_on() -> None:
    assert CommandEncoder().bold(True) == b"\x1bE\x01"

def test_bold_off() -> None:
    assert CommandEncoder().bold(False) == b"\x1bE\x00"

def test_feed_lines() -> None:
    assert CommandEncoder().feed_lines(3) == b"\x1bd\x03"

def test_feed_lines_out_of_range() -> None:
    with pytest.raises(ValueError):
        CommandEncoder().feed_lines(256)
```

---

## Golden byte tests

Golden files capture expected byte output for complete print operations. They are committed binary files.

```python
from pathlib import Path
from mpul465.transports import DryRunTransport

GOLDEN = Path(__file__).parent / "golden"

def test_hello_golden() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.text("Hello\n")
    assert transport.buffer == (GOLDEN / "hello.bin").read_bytes()
```

When a command encoding changes deliberately, regenerate the golden file:

```bash
python -c "
from mpul465 import MPUL465Printer
from mpul465.transports import DryRunTransport

t = DryRunTransport()
with MPUL465Printer(t) as p:
    p.initialize()
    p.text('Hello\n')
open('tests/golden/hello.bin', 'wb').write(t.buffer)
"
```

Commit the updated golden file alongside the code change.

---

## Text engine tests

```python
def test_ascii_prints_native() -> None:
    engine = make_engine(codepage="cp437")
    segments = engine.render_text("Hello\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], NativeTextSegment)
    assert segments[0].data == b"Hello\n"

def test_lambda_renders_raster_in_auto_mode() -> None:
    engine = make_engine(codepage="cp437")
    segments = engine.render_text("λ\n", fallback="auto")
    assert len(segments) == 1
    assert isinstance(segments[0], RasterTextSegment)

def test_strict_mode_rejects_unsupported_char() -> None:
    engine = make_engine(codepage="cp437")
    with pytest.raises(UnsupportedCharacterError) as exc_info:
        engine.render_text("λ\n", fallback="strict")
    assert "λ" in exc_info.value.characters

def test_raster_mode_always_rasterizes() -> None:
    engine = make_engine(codepage="cp437")
    segments = engine.render_text("Hello\n", fallback="raster")
    assert all(isinstance(s, RasterTextSegment) for s in segments)

def test_unsupported_char_does_not_bleed_into_next_line() -> None:
    engine = make_engine(codepage="cp437")
    segments = engine.render_text("λ\nHello\n", fallback="auto")
    # second line should be native
    assert isinstance(segments[-1], NativeTextSegment)
```

---

## Raster pipeline tests

```python
def test_pack_msb_first_width() -> None:
    img = Image.new("1", (384, 1), 0)
    raster = BitPacker().pack_msb_first(img)
    assert raster.width == 384
    assert raster.stride == 48         # ceil(384/8)
    assert len(raster.data) == 48

def test_pack_msb_first_black_pixel() -> None:
    img = Image.new("1", (8, 1), 0)
    img.putpixel((0, 0), 1)            # leftmost pixel black
    raster = BitPacker().pack_msb_first(img)
    assert raster.data[0] == 0b10000000

def test_fit_width_scales_to_dots_per_line() -> None:
    config = MPUL465Config(dots_per_line=384)
    img = Image.new("RGB", (800, 200), "white")
    engine = GraphicsEngine(Rasterizer(), CommandEncoder(), config)
    # should not raise; result width must be 384
    result = engine.image_to_commands(img, width="fit")
    assert isinstance(result, bytes)
    assert len(result) > 0
```

---

## Image tests with tmp_path

Use pytest's `tmp_path` fixture for tests that generate image files:

```python
def test_image_file_roundtrip(tmp_path: Path) -> None:
    img = Image.new("RGB", (100, 50), "white")
    img_path = tmp_path / "test.png"
    img.save(img_path)

    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.image(img_path, width="fit")

    assert len(transport.buffer) > 0
```

---

## Hardware tests

Hardware tests require a printer connected to `/dev/ttyUSB0` (or a path passed via fixture).

```python
import pytest
from mpul465 import MPUL465Printer
from mpul465.transports import SerialTransport

@pytest.fixture
def real_printer(request: pytest.FixtureRequest) -> MPUL465Printer:
    port = request.config.getoption("--port", default="/dev/ttyUSB0")
    return MPUL465Printer(SerialTransport(port))

@pytest.mark.hardware
def test_print_test_page(real_printer: MPUL465Printer) -> None:
    with real_printer as printer:
        printer.initialize()
        printer.print_diagnostics()
        printer.feed(3)

@pytest.mark.hardware
def test_unicode_fallback_on_hardware(real_printer: MPUL465Printer) -> None:
    with real_printer as printer:
        printer.initialize()
        printer.text("Lambda: λ\n")   # should print as raster without error
        printer.feed(2)
```

Add to `conftest.py`:

```python
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--port", default="/dev/ttyUSB0", help="Printer serial port")
```

Run hardware tests:

```bash
pytest -m hardware --port /dev/ttyUSB0
```

---

## Test helpers and fixtures

Define shared fixtures in `tests/conftest.py`:

```python
import pytest
from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.transports import DryRunTransport
from mpul465.text import CodePage, TextEngine, TextRasterizer
from mpul465.text.fonts import FontRegistry

@pytest.fixture
def dry_transport() -> DryRunTransport:
    return DryRunTransport()

@pytest.fixture
def printer(dry_transport: DryRunTransport) -> MPUL465Printer:
    return MPUL465Printer(dry_transport)

@pytest.fixture
def config() -> MPUL465Config:
    return MPUL465Config()

def make_engine(codepage: str = "cp437") -> TextEngine:
    cfg = MPUL465Config(native_codepage=codepage)
    cp = CodePage(codepage)
    rasterizer = TextRasterizer(FontRegistry(), cfg)
    return TextEngine(cp, rasterizer, cfg)
```

---

## What not to test

- The internal behavior of Pillow (it has its own test suite).
- CairoSVG rendering fidelity (out of scope).
- Serial port behavior (pyserial has its own tests).

Test the **boundaries**: what goes into our code, and what bytes come out.
