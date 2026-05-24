# Transports

## Transport protocol

Transport is defined as a `typing.Protocol` — structural subtyping, not inheritance. Any class implementing these three methods qualifies:

```python
from typing import Protocol

class Transport(Protocol):
    def write(self, data: bytes) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...
```

You do not need to inherit from anything to implement a custom transport.

---

## SerialTransport

The primary transport for a physical MPU-L465 connected via USB-to-serial adapter or native serial port.

```python
from mpul465.transports import SerialTransport

transport = SerialTransport(
    port="/dev/ttyUSB0",
    baudrate=115200,
    timeout=2.0,
    write_timeout=2.0,
)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `port` | required | Device path, e.g. `/dev/ttyUSB0`, `/dev/ttyS0` |
| `baudrate` | `115200` | Serial baud rate. Verify against printer DIP switch settings. |
| `timeout` | `2.0` | Read timeout in seconds. |
| `write_timeout` | `2.0` | Write timeout in seconds. |

Backed by `pyserial`. The port is opened on construction and closed by `close()` or the context manager.

### Permissions

On most Linux systems the serial device is owned by the `dialout` group:

```bash
sudo usermod -aG dialout $USER
# log out and back in for group membership to take effect
```

---

## FileTransport

Writes raw bytes to a file path. Useful for Linux raw printer devices (`/dev/usb/lp0`) and for capturing output during debugging.

```python
from mpul465.transports import FileTransport

# Raw USB printer device
transport = FileTransport("/dev/usb/lp0")

# Capture to file for inspection
transport = FileTransport("/tmp/print_job.bin")
```

`flush()` calls the underlying file's `flush()`. `close()` closes the file.

---

## UsbRawTransport

Direct USB access via the raw USB device node, for environments where a serial adapter is not in the path.

```python
from mpul465.transports import UsbRawTransport

transport = UsbRawTransport("/dev/usb/lp0")
```

On Linux, raw USB printer devices typically require the user to be in the `lp` group:

```bash
sudo usermod -aG lp $USER
```

---

## DryRunTransport

Captures all bytes written to it in a buffer. Does not write to any device. The primary transport for unit testing.

```python
from mpul465.transports import DryRunTransport

transport = DryRunTransport()
printer = MPUL465Printer(transport)
printer.initialize()
printer.text("hello")

assert transport.buffer == b"\x1b@hello"
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `buffer` | `bytes` | All bytes written since construction or last `reset()`. |

### Methods

| Method | Description |
|--------|-------------|
| `reset() -> None` | Clears the buffer. |
| `write(data: bytes) -> int` | Appends to buffer; returns `len(data)`. |
| `flush() -> None` | No-op. |
| `close() -> None` | No-op. |

---

## Implementing a custom transport

Any object satisfying the `Transport` protocol works:

```python
class MemoryTransport:
    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.chunks.append(data)
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass
```

No registration or inheritance is required.

---

## Error handling

Transport failures raise `TransportError` (a subclass of `MPUL465Error`). The printer object does not retry on failure. See [docs/exceptions.md](exceptions.md).
