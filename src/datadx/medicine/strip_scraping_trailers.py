"""Medicine: strip_scraping_trailers (C1).

Trims trailing CMS boilerplate, RSS feed credits, and tag clouds at the end of articles.
"""

from __future__ import annotations

from typing import Literal

import regex

from datadx.medicine.base import DocCtx

_TRAILER_PATTERNS = regex.compile(
    r"\n\s*(?:"
    r"Tags\s*:|"
    r"Keywords\s*:|"
    r"टॅग्ज\s*:|"
    r"This News has been Retrieved from RSS|"
    r"All Credits and Copyrights Belongs|"
    r"Previous Article|"
    r"Next Article|"
    r"Related Posts|"
    r"Add A Comment"
    r").*$",
    regex.IGNORECASE | regex.DOTALL,
)


class StripScrapingTrailersMedicine:
    """Trims trailing scraping and CMS boilerplate appended to articles."""

    code: str = "C1"
    name: str = "strip_scraping_trailers"
    action: Literal["fix", "drop"] = "fix"

    def applies(self, text: str, ctx: DocCtx) -> bool:
        return bool(_TRAILER_PATTERNS.search(text))

    def apply(self, text: str, ctx: DocCtx) -> str:
        res = _TRAILER_PATTERNS.sub("", text).rstrip()
        return res if res else text
