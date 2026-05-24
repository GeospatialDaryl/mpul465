# mpul465

Python interface for the SII / Seiko MPU-L465 thermal printer.

Initial goals:

- Native ESC/POS-style text output
- Raster image printing
- SVG/vector-to-raster printing
- Automatic Unicode raster fallback
- Clean class-based Python API

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,svg]"


EFO
