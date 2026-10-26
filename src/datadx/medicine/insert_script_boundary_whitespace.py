"""Medicine: insert_script_boundary_whitespace (A6).

Inserts whitespace at fused Latin-Indic script boundaries caused by HTML tag-drop
or web scraping defects (e.g. 'Articleकसब्याच्या' -> 'Article कसब्याच्या').
"""

from __future__ import annotations

from typing import Literal

import regex

from datadx.medicine.base import DocCtx

_AGGLUTINATED_LATIN_INDIC_RE = regex.compile(
    r"(\p{Latin})(?=[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}])"
)
_AGGLUTINATED_INDIC_LATIN_RE = regex.compile(
    r"([\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}])(?=\p{Latin})"
)


class InsertScriptBoundaryWhitespaceMedicine:
    """Inserts space at agglutinated Latin and Indic script token boundaries."""

    code: str = "A6"
    name: str = "insert_script_boundary_whitespace"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return bool(_AGGLUTINATED_LATIN_INDIC_RE.search(text)) or bool(
            _AGGLUTINATED_INDIC_LATIN_RE.search(text)
        )

    def apply(self, text: str, ctx: DocCtx) -> str:
        text = _AGGLUTINATED_LATIN_INDIC_RE.sub(r"\1 ", text)
        text = _AGGLUTINATED_INDIC_LATIN_RE.sub(r"\1 ", text)
        return text
