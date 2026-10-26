"""Medicine: drop_fffd (A4).

Drops the document when U+FFFD count >= policy threshold (default: 3).
"""

from __future__ import annotations

from typing import Literal

from datadx.medicine.base import DocCtx


class DropFffdMedicine:
    """Drops documents with high counts of replacement character U+FFFD."""

    code: str = "A4"
    name: str = "drop_fffd"
    action: Literal["fix", "drop"] = "drop"
    threshold: int = 3

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return text.count("\ufffd") >= self.threshold

    def apply(self, text: str, ctx: DocCtx) -> str:
        # Drop document (clean_text becomes empty string)
        return ""
