from __future__ import annotations

from mpul465 import MPUL465Printer
from mpul465.transports.dry_run import DryRunTransport


def test_initialize_sends_correct_bytes() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
    assert transport.buffer == b"\x1b@"


def test_feed_appends_after_initialize() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.feed(3)
    assert transport.buffer == b"\x1b@" + b"\x1bd\x03"


def test_text_native_ascii() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.text("Hi\n")
    assert b"Hi\n" in transport.buffer


def test_bold_wraps_text() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
        printer.bold("Bold\n")
    buf = transport.buffer
    bold_on = b"\x1bE\x01"
    bold_off = b"\x1bE\x00"
    assert bold_on in buf
    assert bold_off in buf
    assert buf.index(bold_on) < buf.index(bold_off)


def test_context_manager_closes_transport() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.initialize()
    # DryRunTransport.close() is a no-op; verify no exception was raised


def test_dry_run_buffer_reset() -> None:
    transport = DryRunTransport()
    printer = MPUL465Printer(transport)
    printer.initialize()
    assert len(transport.buffer) > 0
    transport.reset()
    assert transport.buffer == b""
    printer.close()
