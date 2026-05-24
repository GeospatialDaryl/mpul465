from __future__ import annotations

import pytest

from mpul465 import MPUL465Config, MPUL465Printer
from mpul465.commands import CommandEncoder
from mpul465.constants import BarcodeKind
from mpul465.exceptions import CommandNotSupportedError
from mpul465.graphics.qr import QRRasterizer
from mpul465.transports.dry_run import DryRunTransport


# ---------------------------------------------------------------------------
# CommandEncoder.qr — byte structure (hardware verification still required)
# ---------------------------------------------------------------------------

def test_qr_returns_bytes() -> None:
    result = CommandEncoder().qr("https://example.com")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_qr_starts_with_gs_open_k() -> None:
    result = CommandEncoder().qr("A")
    assert result[:3] == b"\x1d(k"


def test_qr_contains_four_gs_open_k_segments() -> None:
    result = CommandEncoder().qr("A")
    assert result.count(b"\x1d(k") == 4  # size, EC, store, print


def test_qr_data_is_embedded_in_output() -> None:
    result = CommandEncoder().qr("HELLO")
    assert b"HELLO" in result


def test_qr_default_module_size_is_3() -> None:
    result = CommandEncoder().qr("X", module_size=3)
    # Size command bytes (after GS(k prefix): pL pH cn fn module_size
    # GS(k is 3 bytes, then pL(+1) pH(+1) cn(+1) fn(+1) module_size(+1) → offset 7
    idx = result.index(b"\x1d(k")
    assert result[idx + 7] == 3


def test_qr_error_correction_m_encodes_as_49() -> None:
    result = CommandEncoder().qr("X", error_correction="M")
    # Split on GS(k prefix; each segment is [pL, pH, cn, fn, param...]
    segments = result.split(b"\x1d(k")[1:]
    ec_segment = segments[1]  # 0=size, 1=EC level
    # EC byte is at index 4: pL(0) pH(1) cn(2) fn(3) ec_byte(4)
    assert ec_segment[4] == 49


def test_qr_error_correction_h_encodes_as_51() -> None:
    result = CommandEncoder().qr("X", error_correction="H")
    segments = result.split(b"\x1d(k")[1:]
    ec_segment = segments[1]
    assert ec_segment[4] == 51


def test_qr_invalid_error_correction_raises() -> None:
    with pytest.raises(ValueError, match="error_correction"):
        CommandEncoder().qr("X", error_correction="Z")


def test_qr_invalid_module_size_raises() -> None:
    with pytest.raises(ValueError, match="module_size"):
        CommandEncoder().qr("X", module_size=0)

    with pytest.raises(ValueError, match="module_size"):
        CommandEncoder().qr("X", module_size=17)


def test_qr_data_length_fields_are_correct() -> None:
    value = "AB"
    result = CommandEncoder().qr(value)
    # Store-data segment: GS ( k pL pH 49 80 48 data
    # len("AB") + 3 = 5 → pL=5, pH=0
    segments = result.split(b"\x1d(k")[1:]
    store_segment = segments[2]
    pL = store_segment[0]
    pH = store_segment[1]
    assert pL + pH * 256 == len(value) + 3


# ---------------------------------------------------------------------------
# CommandEncoder.barcode — byte structure
# ---------------------------------------------------------------------------

def test_barcode_code128_returns_bytes() -> None:
    result = CommandEncoder().barcode("HELLO", BarcodeKind.CODE128)
    assert isinstance(result, bytes)


def test_barcode_starts_with_gs_k() -> None:
    result = CommandEncoder().barcode("123", BarcodeKind.CODE128)
    assert result[:2] == b"\x1dk"


def test_barcode_code128_type_byte_is_73() -> None:
    result = CommandEncoder().barcode("123", BarcodeKind.CODE128)
    assert result[2] == 73


def test_barcode_ean13_type_byte_is_67() -> None:
    result = CommandEncoder().barcode("123456789012", BarcodeKind.EAN13)
    assert result[2] == 67


def test_barcode_ean8_type_byte_is_68() -> None:
    result = CommandEncoder().barcode("1234567", BarcodeKind.EAN8)
    assert result[2] == 68


def test_barcode_code39_type_byte_is_69() -> None:
    result = CommandEncoder().barcode("ABC", BarcodeKind.CODE39)
    assert result[2] == 69


def test_barcode_upca_type_byte_is_65() -> None:
    result = CommandEncoder().barcode("12345678901", BarcodeKind.UPCA)
    assert result[2] == 65


def test_barcode_data_embedded_in_output() -> None:
    result = CommandEncoder().barcode("HELLO", BarcodeKind.CODE128)
    assert b"HELLO" in result


def test_barcode_length_byte_matches_data() -> None:
    data = "HELLO"
    result = CommandEncoder().barcode(data, BarcodeKind.CODE128)
    # GS k m n d1..dn → result[3] = n = len(data)
    assert result[3] == len(data)


# ---------------------------------------------------------------------------
# QRRasterizer — raster fallback
# ---------------------------------------------------------------------------

def test_qr_rasterizer_returns_pil_image() -> None:
    from PIL import Image

    img = QRRasterizer().render("https://example.com")
    assert isinstance(img, Image.Image)


def test_qr_rasterizer_image_is_square() -> None:
    img = QRRasterizer().render("X")
    assert img.width == img.height


def test_qr_rasterizer_image_is_1bit() -> None:
    img = QRRasterizer().render("X")
    assert img.mode == "1"


def test_qr_rasterizer_larger_data_produces_larger_image() -> None:
    small = QRRasterizer().render("X")
    large = QRRasterizer().render("X" * 100)
    assert large.width >= small.width


# ---------------------------------------------------------------------------
# MPUL465Printer — native path (enable_native_qr=True)
# ---------------------------------------------------------------------------

def test_printer_qr_native_sends_gs_open_k() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(enable_native_qr=True)
    with MPUL465Printer(transport, cfg) as printer:
        printer.qr("https://example.com")
    assert b"\x1d(k" in transport.buffer


def test_printer_barcode_native_sends_gs_k() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(enable_native_barcode=True)
    with MPUL465Printer(transport, cfg) as printer:
        printer.barcode("HELLO", BarcodeKind.CODE128)
    assert b"\x1dk" in transport.buffer


# ---------------------------------------------------------------------------
# MPUL465Printer — raster fallback (enable_native_qr=False)
# ---------------------------------------------------------------------------

def test_printer_qr_raster_fallback_sends_gs_v0() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(enable_native_qr=False)
    with MPUL465Printer(transport, cfg) as printer:
        printer.qr("https://example.com")
    assert b"\x1dv0" in transport.buffer


def test_printer_qr_raster_fallback_does_not_send_gs_open_k() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(enable_native_qr=False)
    with MPUL465Printer(transport, cfg) as printer:
        printer.qr("https://example.com")
    assert b"\x1d(k" not in transport.buffer


# ---------------------------------------------------------------------------
# MPUL465Printer — barcode disabled raises CommandNotSupportedError
# ---------------------------------------------------------------------------

def test_printer_barcode_disabled_raises() -> None:
    transport = DryRunTransport()
    cfg = MPUL465Config(enable_native_barcode=False)
    with MPUL465Printer(transport, cfg) as printer:
        with pytest.raises(CommandNotSupportedError):
            printer.barcode("HELLO", BarcodeKind.CODE128)
