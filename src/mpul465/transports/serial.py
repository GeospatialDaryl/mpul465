from __future__ import annotations

import serial  # type: ignore[import-untyped]

from mpul465.exceptions import TransportError


class SerialTransport:
    """Serial port transport backed by pyserial."""

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 2.0,
        write_timeout: float = 2.0,
    ) -> None:
        try:
            self._serial = serial.Serial(
                port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=write_timeout,
            )
        except serial.SerialException as exc:
            raise TransportError(f"Failed to open {port}: {exc}") from exc

    def write(self, data: bytes) -> int:
        try:
            return self._serial.write(data)
        except serial.SerialException as exc:
            raise TransportError(f"Write failed: {exc}") from exc

    def flush(self) -> None:
        try:
            self._serial.flush()
        except serial.SerialException as exc:
            raise TransportError(f"Flush failed: {exc}") from exc

    def close(self) -> None:
        self._serial.close()
