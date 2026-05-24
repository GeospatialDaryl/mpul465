from __future__ import annotations


class CodePage:
    """Tests and encodes characters against a Python codec name (e.g. 'cp437')."""

    def __init__(self, name: str) -> None:
        self.name = name

    def can_encode(self, text: str) -> bool:
        try:
            text.encode(self.name)
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def encode(self, text: str) -> bytes:
        return text.encode(self.name)

    def unsupported_chars(self, text: str) -> set[str]:
        result: set[str] = set()
        for ch in text:
            try:
                ch.encode(self.name)
            except (UnicodeEncodeError, LookupError):
                result.add(ch)
        return result
