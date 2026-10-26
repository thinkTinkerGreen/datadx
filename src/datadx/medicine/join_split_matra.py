"""Medicine: join_split_matra (G1).

Removes corrupt whitespace between an Indic base consonant and following dependent mark.
Critical for restoring Indic script integrity.
"""

from __future__ import annotations

from typing import Literal

from datadx.detectors.damage import G1_SPLIT_MATRA_RE, G1_SPLIT_VISARGA_RE
from datadx.medicine.base import DocCtx


class JoinSplitMatraMedicine:
    """Rejoins base consonants with disconnected vowel marks (matras) and split visargas."""

    code: str = "G1"
    name: str = "join_split_matra"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return bool(G1_SPLIT_MATRA_RE.search(text)) or bool(G1_SPLIT_VISARGA_RE.search(text))

    def apply(self, text: str, ctx: DocCtx) -> str:
        # Rejoin base + mark: group 1 and group 2 concatenated directly
        res = G1_SPLIT_MATRA_RE.sub(r"\1\2", text)
        # Repair split visarga in time notation: ९ ः ३० -> ९:३०
        res = G1_SPLIT_VISARGA_RE.sub(r"\1:\2", res)
        return str(res)
