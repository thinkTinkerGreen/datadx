"""Medicine: remove_ghost_tokens (B3).

Deletes LLM special tokens and chat markers.
Drops the document entirely if ghost tokens exceed 1% of characters.
"""

from __future__ import annotations

from typing import Literal

from datadx.detectors.markup import B3_REGEXES, EXACT_SPECIAL_TOKENS
from datadx.medicine.base import DocCtx


class RemoveGhostTokensMedicine:
    """Removes ghost chat markers and drops heavily contaminated documents."""

    code: str = "B3"
    name: str = "remove_ghost_tokens"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        if any(t in text for t in EXACT_SPECIAL_TOKENS):
            return True
        return any(pat.search(text) for pat in B3_REGEXES)

    def apply(self, text: str, ctx: DocCtx) -> str:
        # Calculate ghost token character impact
        matched_chars = 0
        cleaned = text

        for t in EXACT_SPECIAL_TOKENS:
            count = cleaned.count(t)
            if count > 0:
                matched_chars += count * len(t)
                cleaned = cleaned.replace(t, "")

        for pat in B3_REGEXES:
            matches = list(pat.finditer(cleaned))
            for m in matches:
                matched_chars += len(m.group())
            cleaned = pat.sub("", cleaned)

        # If ghost tokens make up > 1% of characters, drop the document
        if len(text) > 0 and (matched_chars / len(text)) > 0.01:
            return ""

        return cleaned
