"""Medicine: strip_tags (B2).

Strips HTML and XML tags in prose packs. Never applied to markup code packs.
"""

from __future__ import annotations

import re
from typing import Literal

from datadx.medicine.base import DocCtx

TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?/?>|<!--.*?-->", re.DOTALL)


class StripTagsMedicine:
    """Strips HTML/XML tags from prose documents."""

    code: str = "B2"
    name: str = "strip_tags"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        lang = ctx.lang_label.lower()
        source = ctx.source.lower()
        if ("html" in lang or "xml" in lang) and "code" in source:
            return False
        return bool(TAG_RE.search(text))

    def apply(self, text: str, ctx: DocCtx) -> str:
        lang = ctx.lang_label.lower()
        source = ctx.source.lower()
        if ("html" in lang or "xml" in lang) and "code" in source:
            return text
        return TAG_RE.sub("", text)
