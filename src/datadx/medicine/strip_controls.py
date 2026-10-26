"""Medicine: strip_controls (A2).

Deletes A2 control characters (U+0000-001F except tab/newline, U+007F-009F).
Converts CRLF and lone CR to standard Unix newline LF (\n).
"""

from __future__ import annotations

from typing import Literal

from datadx.medicine.base import DocCtx


class StripControlsMedicine:
    """Strips control characters and normalizes newlines."""

    code: str = "A2"
    name: str = "strip_controls"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        if "\r" in text:
            return True
        for ch in text:
            cp = ord(ch)
            if (0 <= cp <= 0x1F and ch not in ("\t", "\n")) or (0x7F <= cp <= 0x9F):
                return True
        return False

    def apply(self, text: str, ctx: DocCtx) -> str:
        # 1. Normalize newlines: \r\n -> \n, lone \r -> \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Filter remaining control characters
        out = []
        for ch in text:
            cp = ord(ch)
            if (0 <= cp <= 0x1F and ch not in ("\t", "\n")) or (0x7F <= cp <= 0x9F):
                continue
            out.append(ch)
        return "".join(out)
