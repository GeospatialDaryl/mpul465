from __future__ import annotations

import pytest

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.text.codepages import CodePage
from mpul465.text.engine import TextEngine, TextRasterizer
from mpul465.text.fonts import FontRegistry
from mpul465.transports.dry_run import DryRunTransport


@pytest.fixture
def dry_transport() -> DryRunTransport:
    return DryRunTransport()


@pytest.fixture
def config() -> MPUL465Config:
    return MPUL465Config()


@pytest.fixture
def printer(dry_transport: DryRunTransport) -> MPUL465Printer:
    return MPUL465Printer(dry_transport)


def make_engine(codepage: str = "cp437") -> TextEngine:
    cfg = MPUL465Config(native_codepage=codepage)
    cp = CodePage(codepage)
    rasterizer = TextRasterizer(FontRegistry(), cfg)
    return TextEngine(cp, rasterizer, cfg)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--port", default="/dev/ttyUSB0", help="Printer serial port for hardware tests")
