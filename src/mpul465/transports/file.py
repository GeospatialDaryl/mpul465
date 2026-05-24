from __future__ import annotations

from pathlib import Path

from mpul465.exceptions import TransportError


class FileTransport:
    """Writes raw bytes to a file path.

    Useful for Linux raw printer devices (/dev/usb/lp0) or capturing output.
    """

    def __init__(self, path: str | Path) -> None:
        try:
            self._file = open(path, "wb")  # noqa: WPS515
        except OSError as exc:
            raise TransportError(f"Failed to open {path}: {exc}") from exc

    def write(self, data: bytes) -> int:
        try:
            return self._file.write(data)
        except OSError as exc:
            raise TransportError(f"Write failed: {exc}") from exc

    def flush(self) -> None:
        try:
            self._file.flush()
        except OSError as exc:
            raise TransportError(f"Flush failed: {exc}") from exc

    def close(self) -> None:
        self._file.close()
