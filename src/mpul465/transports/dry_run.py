from __future__ import annotations


class DryRunTransport:
    """Captures all bytes written to it. Primary transport for unit testing."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def buffer(self) -> bytes:
        return bytes(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()

    def write(self, data: bytes) -> int:
        self._buffer.extend(data)
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass
