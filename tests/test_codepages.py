from __future__ import annotations

from mpul465.text.codepages import CodePage, UnicodePolicy


# ---------------------------------------------------------------------------
# CodePage
# ---------------------------------------------------------------------------

def test_ascii_encodable() -> None:
    cp = CodePage("cp437")
    assert cp.can_encode("Hello, world!")


def test_lambda_not_in_cp437() -> None:
    cp = CodePage("cp437")
    assert not cp.can_encode("λ")


def test_degree_in_cp437() -> None:
    cp = CodePage("cp437")
    assert cp.can_encode("72°F")


def test_unsupported_chars_returns_set() -> None:
    cp = CodePage("cp437")
    result = cp.unsupported_chars("ABC λ DEF ⚙")
    assert "λ" in result
    assert "⚙" in result
    assert "A" not in result


def test_encode_ascii() -> None:
    cp = CodePage("cp437")
    assert cp.encode("Hello") == b"Hello"


def test_empty_string_encodable() -> None:
    cp = CodePage("cp437")
    assert cp.can_encode("")
    assert cp.unsupported_chars("") == set()


# ---------------------------------------------------------------------------
# UnicodePolicy — normalization
# ---------------------------------------------------------------------------

def test_default_policy_is_nfc() -> None:
    policy = UnicodePolicy()
    assert policy.normalize == "NFC"
    assert policy.transliterate is False
    assert policy.replacement == "?"


def test_nfc_normalization_composes_combining_char() -> None:
    # e + combining acute accent (two code points) → é (one code point)
    decomposed = "é"  # e + combining acute
    policy = UnicodePolicy(normalize="NFC")
    result = policy.apply(decomposed)
    assert result == "é"
    assert len(result) == 1


def test_nfkc_maps_compatibility_chars() -> None:
    policy = UnicodePolicy(normalize="NFKC")
    assert policy.apply("ﬁ") == "fi"   # ligature fi → two chars
    assert policy.apply("x²") == "x2"  # superscript → digit


def test_normalize_none_passes_through() -> None:
    decomposed = "é"
    policy = UnicodePolicy(normalize="none")
    assert policy.apply(decomposed) == decomposed


# ---------------------------------------------------------------------------
# UnicodePolicy — transliteration
# ---------------------------------------------------------------------------

def test_transliterate_strips_diacritics() -> None:
    policy = UnicodePolicy(transliterate=True)
    assert policy.apply("café") == "cafe"
    assert policy.apply("naïve") == "naive"
    assert policy.apply("über") == "uber"


def test_transliterate_false_preserves_accents() -> None:
    policy = UnicodePolicy(transliterate=False)
    assert "é" in policy.apply("café")


def test_transliterate_drops_non_latin() -> None:
    policy = UnicodePolicy(transliterate=True)
    # Greek has no ASCII equivalent — dropped entirely
    assert policy.apply("λ") == ""


# ---------------------------------------------------------------------------
# UnicodePolicy — replacement character
# ---------------------------------------------------------------------------

def test_custom_replacement_char() -> None:
    policy = UnicodePolicy(replacement="*")
    assert policy.replacement == "*"
