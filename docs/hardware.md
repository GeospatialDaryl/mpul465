# Hardware Notes

## Device

**SII MPU-L465** — discontinued Seiko Instruments thermal printer. The user guide identifies it as a discontinued unit and refers to a separate technical reference for command-level details. Some command behaviors must therefore be verified empirically rather than assumed from documentation.

---

## Connection

### USB-to-serial adapter (most common)

The MPU-L465 typically exposes a serial interface. Connect via a USB-to-serial adapter:

```
Printer serial port → USB-to-serial adapter → /dev/ttyUSB0
```

Check the assigned device node after plugging in:

```bash
dmesg | grep ttyUSB
ls /dev/ttyUSB*
```

### Permissions

```bash
sudo usermod -aG dialout $USER
# Log out and back in, then verify:
groups | grep dialout
```

### Direct USB device node

If the printer exposes a raw USB device (e.g. via a USB printer class interface):

```bash
ls /dev/usb/lp*
sudo usermod -aG lp $USER
```

---

## Baud rate

The default baud rate in `SerialTransport` is `115200`. This **must be verified** against the printer's DIP switch configuration. Common alternatives: `9600`, `19200`, `38400`, `57600`.

Check the physical DIP switches on the printer body against the printer manual. If you do not have the manual, try common baud rates in sequence using the `self-test` command:

```bash
mpul465 self-test --port /dev/ttyUSB0 --baudrate 9600
mpul465 self-test --port /dev/ttyUSB0 --baudrate 19200
mpul465 self-test --port /dev/ttyUSB0 --baudrate 115200
```

---

## Print width calibration

`MPUL465Config.dots_per_line` defaults to `384`, which is common for 58 mm-class thermal printers, but this value must be verified before relying on it.

### Calibration procedure

1. Print a full-width black bar:

```python
from mpul465 import MPUL465Printer, MPUL465Config
from mpul465.transports import SerialTransport
from PIL import Image

config = MPUL465Config(dots_per_line=384)
with MPUL465Printer(SerialTransport("/dev/ttyUSB0"), config) as printer:
    printer.initialize()
    # Full-width black bar
    img = Image.new("1", (384, 10), 0)   # all black
    printer.image(img)
    printer.feed(3)
```

2. Observe the printed output:
   - If the bar reaches both edges exactly: `dots_per_line=384` is correct.
   - If the bar is narrower than the paper: increase `dots_per_line`.
   - If the image wraps or clips: decrease `dots_per_line`.

3. Use the diagnostic print page, which includes a raster test pattern:

```bash
mpul465 self-test --port /dev/ttyUSB0
```

### Known values

| Width (mm) | Common dots_per_line |
|------------|----------------------|
| 58 mm | 384 |
| 80 mm | 576 |

Update this table with the confirmed value for this unit.

---

## Native column count

The number of native text columns depends on the active printer font. Verify with a test print:

```python
printer.text("0" * 40 + "\n")   # try 32, 40, 48 characters
printer.text("0" * 32 + "\n")
```

If the first line wraps and the second does not, `columns_normal` is 32. Document the confirmed value in `NativeFontMetrics`.

---

## Command verification

The following commands must be verified on the actual hardware before marking their unit tests as stable. Add results to this table.

| Command | ESC/POS form | Verified | Notes |
|---------|-------------|----------|-------|
| Initialize | `ESC @` | — | |
| Feed lines | `ESC d n` | — | |
| Bold on/off | `ESC E n` | — | |
| Underline on/off | `ESC - n` | — | |
| Alignment | `ESC a n` | — | |
| Raster image | `GS v 0` | — | Also check `ESC *` variant |
| Native QR | — | — | Format unknown; verify or disable |
| Native barcode | — | — | Supported types unknown |
| Code page select | `ESC t n` | — | Verify page IDs |

Mark verified commands with the date and the byte sequence that was confirmed to work. If a command does not work as documented, note the correct byte sequence.

---

## Self-test output

The printer's built-in self-test (hold feed button during power-on, typically) prints its firmware version, DIP switch states, and configured parameters. Photograph or transcribe this output — it is the ground truth for baud rate, code page, and print width.

---

## Known quirks

_Document empirically discovered behaviors here as the library is developed._

- [ ] Confirm whether `ESC @` resets code page selection.
- [ ] Confirm whether the printer requires a final `LF` after the last raster band.
- [ ] Confirm maximum safe raster band height (`image_chunk_height`).
- [ ] Confirm whether native QR is available and which QR command format the printer accepts.

---

## Diagnostic print page

The library's diagnostic page prints a structured self-test to the printer:

```bash
mpul465 self-test --port /dev/ttyUSB0
```

Or programmatically:

```python
printer.print_diagnostics()
```

The page includes:

- Library version
- Transport device path
- Configured `dots_per_line`
- Native code page
- Black/white raster pattern (for width verification)
- Unicode fallback samples (ASCII native, λ raster, ⚙ raster)
- QR code test

Run this page first when connecting to a new unit.
