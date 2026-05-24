from __future__ import annotations


class MPUL465Error(Exception):
    """Base class for all mpul465 exceptions."""


class TransportError(MPUL465Error):
    """Raised when the transport fails to write, flush, or close."""


class PrinterNotReadyError(MPUL465Error):
    """Raised when the printer is addressed before initialize() or signals not-ready."""


class UnsupportedCharacterError(MPUL465Error):
    """Raised in strict fallback mode when text contains characters outside the native code page."""

    def __init__(self, message: str, *, characters: set[str], fallback: str) -> None:
        super().__init__(message)
        self.characters = characters
        self.fallback = fallback


class CommandNotSupportedError(MPUL465Error):
    """Raised when a command is not supported by the hardware configuration."""


class GraphicsRenderError(MPUL465Error):
    """Base class for graphics pipeline errors."""


class SVGRenderError(GraphicsRenderError):
    """Raised when the SVG renderer fails to parse or render input."""


class ImageTooWideError(GraphicsRenderError):
    """Raised when an image exceeds config.dots_per_line and clipping is not permitted."""

    def __init__(self, message: str, *, image_width: int, print_width: int) -> None:
        super().__init__(message)
        self.image_width = image_width
        self.print_width = print_width
