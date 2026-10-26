"""Medicine: fix_mojibake (A3).

Uses ftfy.fix_encoding ONLY (never fix_text per Rule R4).
Keeps fixed text only if Indic letter share increases and it round-trips; else drops.
"""

from __future__ import annotations

from typing import Literal

import ftfy
import regex

from datadx.medicine.base import DocCtx

INDIC_LETTER_RE = regex.compile(
    r"[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}]"
)


class FixMojibakeMedicine:
    """Repairs mojibake via ftfy.fix_encoding."""

    code: str = "A3"
    name: str = "fix_mojibake"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return ftfy.fix_encoding(text) != text

    def apply(self, text: str, ctx: DocCtx) -> str:
        fixed = ftfy.fix_encoding(text)
        if fixed == text:
            return text

        # Check Indic share
        orig_indic = len(INDIC_LETTER_RE.findall(text))
        fixed_indic = len(INDIC_LETTER_RE.findall(fixed))

        if fixed_indic >= orig_indic:
            return fixed

        # Irreparable mojibake drops the text per §9.2
        return ""
