"""Medicine: nfc (A5).

Normalizes text to Unicode Normal Form C (NFC) strictly per Rule R4.
Banned everywhere: NFKC, NFKD, ASCII-folding, lowercasing.
"""

from __future__ import annotations

import unicodedata
from typing import Literal

from datadx.medicine.base import DocCtx


class NfcMedicine:
    """Applies canonical NFC normalization."""

    code: str = "A5"
    name: str = "nfc"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return unicodedata.normalize("NFC", text) != text

    def apply(self, text: str, ctx: DocCtx) -> str:
        return unicodedata.normalize("NFC", text)
