"""Medicine: drop_exact_dupes (H1).

Drops non-original exact duplicate documents in the pack.
"""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Literal

from datadx.medicine.base import DocCtx


class DropExactDupesMedicine:
    """Drops exact duplicate documents."""

    code: str = "H1"
    name: str = "drop_exact_dupes"
    action: Literal["drop", "fix"] = "drop"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        exact_map = ctx.meta.get("exact_hash_map", {})
        norm = unicodedata.normalize("NFC", text)
        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if h in exact_map:
            orig_idx, _ = exact_map[h]
            return bool(orig_idx < ctx.row_index)
        return False

    def apply(self, text: str, ctx: DocCtx) -> str:
        # Drop document
        return ""
