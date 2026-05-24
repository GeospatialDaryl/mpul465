from __future__ import annotations

from mpul465.text.codepages import CodePage


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
