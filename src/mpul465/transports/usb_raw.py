from __future__ import annotations

from pathlib import Path

from mpul465.transports.file import FileTransport


class UsbRawTransport(FileTransport):
    """Direct USB device node transport (e.g. /dev/usb/lp0).

    Requires the user to be in the 'lp' group on Linux.
    """

    def __init__(self, path: str | Path = "/dev/usb/lp0") -> None:
        super().__init__(path)
