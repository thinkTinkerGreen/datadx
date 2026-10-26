"""Medicine: unescape_entities (B1).

Unescapes HTML entities in prose text using html.unescape.
Skipped for code packs where HTML-like markup is expected.
"""

from __future__ import annotations

import html
from typing import Literal

from datadx.medicine.base import DocCtx


class UnescapeEntitiesMedicine:
    """Unescapes HTML entities (&amp;, &nbsp;, numeric references)."""

    code: str = "B1"
    name: str = "unescape_entities"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        lang = ctx.lang_label.lower()
        source = ctx.source.lower()
        if ("html" in lang or "xml" in lang) and "code" in source:
            return False
        return "&" in text and html.unescape(text) != text

    def apply(self, text: str, ctx: DocCtx) -> str:
        lang = ctx.lang_label.lower()
        source = ctx.source.lower()
        if ("html" in lang or "xml" in lang) and "code" in source:
            return text
        return html.unescape(text)
