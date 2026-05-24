from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class UnicodePolicy:
    """Controls Unicode normalization and transliteration before encoding.

    normalize:
        "NFC"  — compose combining chars (default; é+combining → é)
        "NFKC" — additionally map compatibility chars (ﬁ → fi, ² → 2)
        "none" — pass text through unchanged

    transliterate:
        Opt-in, lossy. Strips diacritics so é → e, ü → u.
        Acceptable for simple receipts; wrong for names, labels, or data.

    replacement:
        Substituted for each unsupported character in "native" fallback mode.
    """

    normalize: Literal["none", "NFC", "NFKC"] = "NFC"
    transliterate: bool = False
    replacement: str = "?"

    def apply(self, text: str) -> str:
        if self.normalize != "none":
            text = unicodedata.normalize(self.normalize, text)
        if self.transliterate:
            # NFKD decomposes diacritics into base + combining mark;
            # encoding to ASCII with 'ignore' then drops the combining marks.
            text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return text


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
