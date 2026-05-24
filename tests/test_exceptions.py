from __future__ import annotations

import pytest

from mpul465.exceptions import (
    MPUL465Error,
    CommandNotSupportedError,
    GraphicsRenderError,
    ImageTooWideError,
    PrinterNotReadyError,
    SVGRenderError,
    TransportError,
    UnsupportedCharacterError,
)


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

def test_transport_error_is_mpul465_error() -> None:
    assert issubclass(TransportError, MPUL465Error)


def test_printer_not_ready_is_mpul465_error() -> None:
    assert issubclass(PrinterNotReadyError, MPUL465Error)


def test_command_not_supported_is_mpul465_error() -> None:
    assert issubclass(CommandNotSupportedError, MPUL465Error)


def test_unsupported_character_error_is_mpul465_error() -> None:
    assert issubclass(UnsupportedCharacterError, MPUL465Error)


def test_graphics_render_error_is_mpul465_error() -> None:
    assert issubclass(GraphicsRenderError, MPUL465Error)


def test_svg_render_error_is_graphics_render_error() -> None:
    assert issubclass(SVGRenderError, GraphicsRenderError)


def test_image_too_wide_is_graphics_render_error() -> None:
    assert issubclass(ImageTooWideError, GraphicsRenderError)


# ---------------------------------------------------------------------------
# UnsupportedCharacterError attributes
# ---------------------------------------------------------------------------

def test_unsupported_character_error_carries_characters() -> None:
    exc = UnsupportedCharacterError(
        "unsupported", characters={"λ", "⚙"}, fallback="strict"
    )
    assert "λ" in exc.characters
    assert "⚙" in exc.characters


def test_unsupported_character_error_carries_fallback() -> None:
    exc = UnsupportedCharacterError(
        "unsupported", characters={"λ"}, fallback="strict"
    )
    assert exc.fallback == "strict"


def test_unsupported_character_error_message_accessible() -> None:
    exc = UnsupportedCharacterError(
        "bad chars: λ", characters={"λ"}, fallback="strict"
    )
    assert "bad chars" in str(exc)


# ---------------------------------------------------------------------------
# ImageTooWideError attributes
# ---------------------------------------------------------------------------

def test_image_too_wide_carries_widths() -> None:
    exc = ImageTooWideError("too wide", image_width=500, print_width=384)
    assert exc.image_width == 500
    assert exc.print_width == 384


def test_image_too_wide_message_accessible() -> None:
    exc = ImageTooWideError("image 500px > 384px", image_width=500, print_width=384)
    assert "500" in str(exc) or "image" in str(exc)


# ---------------------------------------------------------------------------
# All exceptions are catchable as MPUL465Error
# ---------------------------------------------------------------------------

def test_all_exceptions_catchable_as_base() -> None:
    exceptions = [
        TransportError("t"),
        PrinterNotReadyError("p"),
        CommandNotSupportedError("c"),
        UnsupportedCharacterError("u", characters=set(), fallback="strict"),
        GraphicsRenderError("g"),
        SVGRenderError("s"),
        ImageTooWideError("i", image_width=1, print_width=1),
    ]
    for exc in exceptions:
        assert isinstance(exc, MPUL465Error), f"{type(exc)} not caught as MPUL465Error"
