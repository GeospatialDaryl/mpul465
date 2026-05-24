from __future__ import annotations

from pathlib import Path

import pytest

from mpul465.exceptions import TransportError
from mpul465.transports.dry_run import DryRunTransport
from mpul465.transports.file import FileTransport


# ---------------------------------------------------------------------------
# DryRunTransport
# ---------------------------------------------------------------------------

def test_dry_run_buffer_starts_empty() -> None:
    t = DryRunTransport()
    assert t.buffer == b""


def test_dry_run_write_returns_byte_count() -> None:
    t = DryRunTransport()
    n = t.write(b"hello")
    assert n == 5


def test_dry_run_write_accumulates() -> None:
    t = DryRunTransport()
    t.write(b"AB")
    t.write(b"CD")
    assert t.buffer == b"ABCD"


def test_dry_run_flush_does_not_raise() -> None:
    t = DryRunTransport()
    t.flush()  # must not raise


def test_dry_run_close_does_not_raise() -> None:
    t = DryRunTransport()
    t.close()  # must not raise


def test_dry_run_reset_clears_buffer() -> None:
    t = DryRunTransport()
    t.write(b"data")
    t.reset()
    assert t.buffer == b""


def test_dry_run_buffer_property_returns_immutable_bytes() -> None:
    t = DryRunTransport()
    t.write(b"x")
    buf = t.buffer
    assert isinstance(buf, bytes)


def test_dry_run_write_empty_returns_zero() -> None:
    t = DryRunTransport()
    assert t.write(b"") == 0


# ---------------------------------------------------------------------------
# FileTransport
# ---------------------------------------------------------------------------

def test_file_transport_raises_transport_error_on_bad_path() -> None:
    with pytest.raises(TransportError):
        FileTransport("/nonexistent/path/that/cannot/be/created/file.bin")


def test_file_transport_write_persists_to_disk(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(out)
    t.write(b"\x1b@Hello\n")
    t.close()
    assert out.read_bytes() == b"\x1b@Hello\n"


def test_file_transport_write_returns_byte_count(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(out)
    n = t.write(b"abc")
    t.close()
    assert n == 3


def test_file_transport_multiple_writes_concatenate(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(out)
    t.write(b"foo")
    t.write(b"bar")
    t.close()
    assert out.read_bytes() == b"foobar"


def test_file_transport_flush_does_not_raise(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(out)
    t.write(b"x")
    t.flush()
    t.close()


def test_file_transport_accepts_path_object(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(out)  # Path object, not str
    t.write(b"ok")
    t.close()
    assert out.exists()


def test_file_transport_accepts_str_path(tmp_path: Path) -> None:
    out = tmp_path / "out.bin"
    t = FileTransport(str(out))  # str path
    t.write(b"ok")
    t.close()
    assert out.exists()
