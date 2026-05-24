from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Structural interface for all printer transports.

    Any class implementing write/flush/close satisfies this protocol
    without inheriting from it.
    """

    def write(self, data: bytes) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...
