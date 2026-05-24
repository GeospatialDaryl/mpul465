# Contributing

## Setup

```bash
git clone <repo>
cd mpul465

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with all dev and optional dependencies
pip install -e ".[dev,svg]"
```

## Development commands

```bash
# Run all unit tests (no hardware required)
pytest

# Run a single test file
pytest tests/test_commands.py

# Run a single test
pytest tests/test_commands.py::test_initialize_command

# Run hardware tests (requires printer on /dev/ttyUSB0)
pytest -m hardware

# Skip hardware tests
pytest -m "not hardware"

# Lint
ruff check src tests

# Format
ruff format src tests

# Type check
mypy src

# Run all checks in one go
ruff check src tests && ruff format --check src tests && mypy src && pytest
```

## Project layout

```
src/mpul465/          Library source
tests/                Unit tests (no hardware)
tests/golden/         Expected byte output (committed binary files)
docs/                 Reference documentation
examples/             Runnable example scripts
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the layers fit together.

## Adding a command

1. Add the method to `CommandEncoder` in `src/mpul465/commands.py`. It must return `bytes`.
2. Add symbolic constants to `src/mpul465/constants.py` if needed.
3. Add a unit test in `tests/test_commands.py` asserting the exact byte output.
4. If the command behavior is uncertain until tested on hardware, note it in [docs/hardware.md](docs/hardware.md).

## Adding a transport

Implement `write(data: bytes) -> int`, `flush() -> None`, and `close() -> None`. No inheritance needed — the `Transport` type is a `typing.Protocol`. Add the implementation in `src/mpul465/transports/`.

## Updating golden files

When a command encoding changes deliberately, regenerate the affected golden file:

```bash
python scripts/regen_golden.py hello   # or whichever golden file changed
```

Commit the updated binary file alongside the code change.

## Code style

- Line length: 100 characters (`ruff`)
- Formatter: `ruff format` (Black-compatible)
- Linting: `ruff check` with `E`, `F`, `I`, `B`, `UP`, `SIM` rules
- Type checking: `mypy` in strict mode

No comments unless the why is non-obvious. No docstrings on methods whose names already communicate their purpose.

## Dependency policy

- Required dependencies: `pyserial`, `Pillow` only.
- SVG support: `CairoSVG` in the `svg` optional group.
- No new required dependencies without discussion.
- Do not bundle font files.

## Hardware testing

Use `@pytest.mark.hardware` for any test that requires a physical printer. These tests are excluded from CI by default. Document results in [docs/hardware.md](docs/hardware.md) as commands are verified.
