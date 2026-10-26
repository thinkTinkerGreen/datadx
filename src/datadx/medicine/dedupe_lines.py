"""Medicine: dedupe_lines (C2).

Removes consecutive or intra-document duplicate lines while preserving first occurrence.
"""

from __future__ import annotations

import unicodedata
from typing import Literal

from datadx.medicine.base import DocCtx


class DedupeLinesMedicine:
    """Deduplicates repeated lines within a document."""

    code: str = "C2"
    name: str = "dedupe_lines"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return False
        norm_lines = [unicodedata.normalize("NFC", line_str) for line_str in lines]
        return len(norm_lines) != len(set(norm_lines))

    def apply(self, text: str, ctx: DocCtx) -> str:
        lines = text.splitlines()
        seen: set[str] = set()
        kept: list[str] = []

        for line in lines:
            norm = unicodedata.normalize("NFC", line.strip())
            if not norm:
                kept.append(line)
                continue
            if norm not in seen:
                seen.add(norm)
                kept.append(line)

        return "\n".join(kept)
