"""Unit tests for view_pack.py (escapes, tail block, hex paging)."""

from diagnosis.tools.view_pack import VISIBLE, hexdump, show


def test_visible_keys_are_unicode_escapes():
    # Ensure VISIBLE dictionary keys match code points
    assert VISIBLE["\u200b"] == "⟦ZWSP⟧"
    assert VISIBLE["\u200c"] == "⟦ZWNJ⟧"
    assert VISIBLE["\u200d"] == "⟦ZWJ⟧"
    assert VISIBLE["\ufeff"] == "⟦BOM⟧"


def test_show_highlights_invisible():
    text = "Hello\u200bWorld\ufeff!"
    displayed = show(text)
    assert "⟦ZWSP⟧" in displayed
    assert "⟦BOM⟧" in displayed


def test_show_grapheme_clusters():
    text = "कशोर"
    displayed = show(text, show_graphemes=True)
    assert "[" in displayed and "]" in displayed


def test_hexdump_paging():
    text = "A" * 5000 + "\u200b"
    # First page: offset 0 to 2000
    p1 = hexdump(text, offset=0, limit=2000)
    assert "chars 0 to 2000" in p1
    # Second page: offset 4000 to 6000
    p2 = hexdump(text, offset=4000, limit=2000)
    assert "chars 4000 to 5001" in p2
    assert "U+200B" in p2
