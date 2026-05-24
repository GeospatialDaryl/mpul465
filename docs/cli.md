# CLI Reference

The `mpul465` command-line tool is installed as a script entry point from `pyproject.toml`:

```toml
[project.scripts]
mpul465 = "mpul465.cli:main"
```

All subcommands accept `--port` to specify the serial device. The library itself never prints directly; the CLI is the only place that uses `print()`.

---

## Global options

| Option | Default | Description |
|--------|---------|-------------|
| `--port PATH` | `/dev/ttyUSB0` | Serial device path |
| `--baudrate INT` | `115200` | Serial baud rate |
| `--dots INT` | `384` | Printer width in dots (overrides config default) |
| `--codepage STR` | `cp437` | Native code page name |

---

## Subcommands

### `print-text`

Print a text string.

```bash
mpul465 print-text --port /dev/ttyUSB0 "Hello, world"
mpul465 print-text --port /dev/ttyUSB0 "λ = wavelength"
mpul465 print-text --port /dev/ttyUSB0 --fallback raster "café"
mpul465 print-text --port /dev/ttyUSB0 --fallback strict "λ"  # exits non-zero if unsupported
mpul465 print-text --port /dev/ttyUSB0 --feed 3 "Hello"       # feed 3 lines after
```

| Option | Default | Description |
|--------|---------|-------------|
| `--fallback MODE` | `auto` | `auto`, `native`, `raster`, `strict` |
| `--feed INT` | `0` | Lines to feed after text |
| `--dump-bytes` | off | Print hex byte dump to stdout instead of sending to printer |

### `print-image`

Print a raster image.

```bash
mpul465 print-image --port /dev/ttyUSB0 logo.png
mpul465 print-image --port /dev/ttyUSB0 logo.png --width fit
mpul465 print-image --port /dev/ttyUSB0 logo.png --width 256
mpul465 print-image --port /dev/ttyUSB0 logo.png --dither none
```

| Option | Default | Description |
|--------|---------|-------------|
| `--width MODE` | `None` | `fit`, an integer pixel width, or omit for natural width |
| `--dither MODE` | `floyd-steinberg` | `floyd-steinberg` or `none` |
| `--feed INT` | `0` | Lines to feed after image |

### `print-svg`

Print an SVG file. Requires `pip install "mpul465[svg]"`.

```bash
mpul465 print-svg --port /dev/ttyUSB0 logo.svg
mpul465 print-svg --port /dev/ttyUSB0 logo.svg --width fit
```

| Option | Default | Description |
|--------|---------|-------------|
| `--width MODE` | `None` | Same as `print-image` |
| `--feed INT` | `0` | Lines to feed after image |

If the `svg` optional dependency is not installed, the command exits with a clear error message.

### `self-test`

Print the diagnostic page.

```bash
mpul465 self-test --port /dev/ttyUSB0
mpul465 self-test --port /dev/ttyUSB0 --feed 5
```

Prints library version, transport, configured width, code page, raster test pattern, Unicode fallback samples, and a QR code. Use this for hardware bring-up and after configuration changes.

### `dump`

Capture and display the raw bytes that would be sent for an operation, without connecting to a printer.

```bash
mpul465 dump print-text "Hello"
mpul465 dump print-image logo.png --width fit
```

Output is a hex dump to stdout. Useful for verifying command encoding and debugging without hardware.

The `--dump-bytes` flag on `print-text` is equivalent for text operations.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (transport failure, render error) |
| `2` | Usage error (invalid arguments) |
| `3` | Unsupported character in `strict` mode |

---

## Examples

```bash
# Basic hello world
mpul465 print-text --port /dev/ttyUSB0 "Hello from Python"

# Print with Unicode (auto fallback)
mpul465 print-text --port /dev/ttyUSB0 "Temperature: 72°F"
mpul465 print-text --port /dev/ttyUSB0 "Lambda: λ"

# Print logo, fit to paper width
mpul465 print-image --port /dev/ttyUSB0 logo.png --width fit

# Print SVG
mpul465 print-svg --port /dev/ttyUSB0 logo.svg --width fit

# Run hardware self-test
mpul465 self-test --port /dev/ttyUSB0

# Inspect bytes without a printer
mpul465 dump print-text "Hello"
mpul465 dump print-image logo.png --width fit
```
