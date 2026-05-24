from __future__ import annotations

from mpul465.printer import MPUL465Printer


def run_diagnostics(printer: MPUL465Printer) -> None:
    """Print a structured self-test page. Delegates to printer.print_diagnostics()."""
    printer.print_diagnostics()
