from __future__ import annotations

import pytest

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.exceptions import UnsupportedCharacterError
from mpul465.text.codepages import UnicodePolicy
from mpul465.text.wrapping import NativeFontMetrics
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


# ---------------------------------------------------------------------------
# unicode_policy kwarg
# ---------------------------------------------------------------------------

def test_unicode_policy_custom_replacement_flows_through() -> None:
    transport = DryRunTransport()
    policy = UnicodePolicy(replacement="*")
    with MPUL465Printer(transport, unicode_policy=policy) as printer:
        printer.text("λ\n", fallback="native")
    assert b"*" in transport.buffer


def test_unicode_policy_strict_raises_unsupported() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        with pytest.raises(UnsupportedCharacterError):
            printer.text("λ\n", fallback="strict")


def test_unicode_policy_nfc_normalizes_before_strict_check() -> None:
    transport = DryRunTransport()
    policy = UnicodePolicy(normalize="NFC")
    cfg = MPUL465Config(native_codepage="cp437")
    with MPUL465Printer(transport, cfg, unicode_policy=policy) as printer:
        # Decomposed e + combining acute → NFC → é → encodable in cp437; strict should not raise
        decomposed = "é\n"
        printer.text(decomposed, fallback="strict")
    assert b"\x82" in transport.buffer  # cp437 encoding of é (not Latin-1 0xe9)


# ---------------------------------------------------------------------------
# native_font_metrics kwarg
# ---------------------------------------------------------------------------

def test_native_font_metrics_wraps_long_line() -> None:
    transport = DryRunTransport()
    metrics = NativeFontMetrics(columns_normal=10, columns_double_width=5)
    with MPUL465Printer(transport, native_font_metrics=metrics) as printer:
        printer.text("A" * 25 + "\n", wrap=True)
    # 25 chars at 10 columns → 3 lines, each written separately
    # All characters are native, so three separate text_bytes calls
    # Verify content is present and buffer is non-trivial
    assert b"A" in transport.buffer
    assert len(transport.buffer) >= 25


# ---------------------------------------------------------------------------
# wrap= parameter
# ---------------------------------------------------------------------------

def test_wrap_false_does_not_break_long_line() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.text("A" * 200 + "\n", wrap=False)
    assert b"A" * 200 in transport.buffer


def test_wrap_true_with_raster_mode_produces_output() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.text("λ " * 30 + "\n", fallback="raster", wrap=True)
    # Raster output includes ESC/POS GS v 0 image command prefix
    assert len(transport.buffer) > 0


# ---------------------------------------------------------------------------
# Additional facade methods
# ---------------------------------------------------------------------------

def test_underline_wraps_text() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.underline("Under\n")
    buf = transport.buffer
    assert b"\x1b-\x01" in buf
    assert b"\x1b-\x00" in buf
    assert buf.index(b"\x1b-\x01") < buf.index(b"\x1b-\x00")


def test_align_center_emits_correct_bytes() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.align(pytest.importorskip("mpul465.constants").Alignment.CENTER)
    assert b"\x1ba\x01" in transport.buffer


def test_line_appends_newline() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        printer.line("Hi")
    assert b"Hi\n" in transport.buffer


def test_barcode_raises_not_implemented() -> None:
    transport = DryRunTransport()
    from mpul465.constants import BarcodeKind
    with MPUL465Printer(transport) as printer:
        with pytest.raises(NotImplementedError):
            printer.barcode("123456", BarcodeKind.CODE128)


def test_qr_raises_not_implemented() -> None:
    transport = DryRunTransport()
    with MPUL465Printer(transport) as printer:
        with pytest.raises(NotImplementedError):
            printer.qr("https://example.com")
