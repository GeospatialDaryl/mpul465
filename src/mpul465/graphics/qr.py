from __future__ import annotations

from PIL import Image

from mpul465.exceptions import CommandNotSupportedError


class QRRasterizer:
    """Generates a QR code as a 1-bit PIL Image using the qrcode library.

    Requires the 'barcodes' optional dependency:
        pip install 'mpul465[barcodes]'
    """

    def render(self, value: str, *, box_size: int = 10, border: int = 4) -> Image.Image:
        try:
            import qrcode  # type: ignore[import-untyped]
            import qrcode.constants  # type: ignore[import-untyped]
        except ImportError as exc:
            raise CommandNotSupportedError(
                "Raster QR requires 'mpul465[barcodes]': "
                "pip install 'mpul465[barcodes]'"
            ) from exc

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(value)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").get_image()
