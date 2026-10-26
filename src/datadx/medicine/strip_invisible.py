"""Medicine: strip_invisible (A1).

Deletes A1 invisible junk characters.
Enforces Rule R3: Strictly PRESERVES ZWJ (U+200D) and ZWNJ (U+200C).
"""

from __future__ import annotations

from typing import Literal

from datadx.medicine.base import DocCtx

# A1 characters to remove (ZWJ \u200d and ZWNJ \u200c are strictly EXCLUDED per Rule R3)
BANNED_INVISIBLE = {
    "\u200b",
    "\ufeff",
    "\u00ad",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}


class StripInvisibleMedicine:
    """Strips invisible junk characters while preserving Indic joiners."""

    code: str = "A1"
    name: str = "strip_invisible"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return any(c in BANNED_INVISIBLE for c in text)

    def apply(self, text: str, ctx: DocCtx) -> str:
        # Fast filter preserving all characters except BANNED_INVISIBLE
        return "".join(c for c in text if c not in BANNED_INVISIBLE)
