"""Medicine: normalize_devanagari_punctuation (G4).

Normalizes ASCII pipe '|' used in place of Devanagari danda '।' without mutating markdown tables.
"""

from __future__ import annotations

from typing import Literal

import regex

from datadx.detectors.damage import G4_PIPE_AS_DANDA_RE
from datadx.medicine.base import DocCtx


class NormalizeDevanagariPunctuationMedicine:
    """Normalizes ASCII pipe substitutes to Devanagari danda punctuation."""

    code: str = "G4"
    name: str = "normalize_devanagari_punctuation"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        if "|" not in text:
            return False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                continue
            if G4_PIPE_AS_DANDA_RE.search(line):
                return True
        return False

    def apply(self, text: str, ctx: DocCtx) -> str:
        lines = text.splitlines(keepends=True)
        out_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                out_lines.append(line)
            else:
                line_norm = regex.sub(
                    r"(?<=[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}\p{M}])\s*\|\|\s*",
                    " ॥ ",
                    line,
                )
                line_norm = G4_PIPE_AS_DANDA_RE.sub(" । ", line_norm)
                out_lines.append(line_norm)
        return "".join(out_lines)
