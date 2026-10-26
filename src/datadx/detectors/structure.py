"""Detectors for Group C: Document Structure (C1 to C5).

Implements boilerplate detection, repeated lines, truncated docs, joined documents,
and keyword lists.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from typing import Any

import regex

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

# Allowed sentence terminators for Indic and Western prose
SENTENCE_TERMINATORS = set(".!?।॥۔؟…\"'”’) ]}»")

# CMS navigation and RSS boilerplate lines
CMS_BOILERPLATE_LINE_RE = regex.compile(
    r"^\s*(?:"
    r"Previous Article.*|"
    r"Next Article.*|"
    r"Related Posts\s*|"
    r"Add A Comment\s*|"
    r"This News has been Retrieved from RSS.*|"
    r"All Credits and Copyrights Belongs.*|"
    r"Share on WhatsApp|"
    r"Follow us on (?:Twitter|Facebook|Instagram)|"
    r"वाचा विश्वासार्ह मराठी न्यूज वेबसाइट.*"
    r")$",
    regex.IGNORECASE,
)

# Tag cloud and SEO keyword lines
TAG_CLOUD_LINE_RE = regex.compile(
    r"^\s*(?:Tags|Keywords|टॅग्ज|महत्त्वाचे टॅग्ज)\s*:.*$",
    regex.IGNORECASE,
)


@register_detector("C1")
def detect_c1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect boilerplate lines (menus, cookie banners, share links, CMS navigation)."""
    findings: list[Finding] = []
    # Check pack-level repetition if provided in ctx
    pack_repeated_lines: set[str] = ctx.get("pack_repeated_short_lines", set())

    lines = text.splitlines()
    offset = 0
    for line in lines:
        line_len = len(line)
        norm_line = unicodedata.normalize("NFC", line.strip())
        tokens = norm_line.split()
        if len(tokens) <= 4 and norm_line in pack_repeated_lines:
            findings.append(
                Finding(
                    code="C1",
                    start=offset,
                    end=offset + line_len,
                    kind="boilerplate_pack_menu",
                    confidence=0.8,
                    auto=False,  # Human judgement required
                    note=f"line:{norm_line[:30]}",
                )
            )
        elif CMS_BOILERPLATE_LINE_RE.match(line):
            findings.append(
                Finding(
                    code="C1",
                    start=offset,
                    end=offset + line_len,
                    kind="cms_navigation_boilerplate",
                    confidence=0.9,
                    auto=False,
                    note="cms navigation boilerplate",
                )
            )
        offset += line_len + 1
    return findings


@register_detector("C2")
def detect_c2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect repeated lines within a document."""
    findings: list[Finding] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return findings

    norm_lines = [" ".join(unicodedata.normalize("NFC", line).split()) for line in lines]
    counts = Counter(norm_lines)

    # Check >= 3 repetitions of a line of >= 4 characters
    repeated_lines = {line for line, count in counts.items() if count >= 3 and len(line) >= 4}

    # Check >= 30% duplicate ratio
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    dup_ratio = duplicate_count / len(lines)

    if repeated_lines or dup_ratio >= 0.30:
        findings.append(
            Finding(
                code="C2",
                start=0,
                end=min(len(text), 100),
                kind="repeated_lines",
                confidence=1.0,
                auto=True,
                note=f"dup_ratio={dup_ratio:.2f};repeated_types={len(repeated_lines)}",
            )
        )
    return findings


@register_detector("C3")
def detect_c3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect truncated documents (stops in middle of sentence or code block)."""
    findings: list[Finding] = []
    stripped = text.strip()
    if not stripped:
        return findings

    last_char = stripped[-1]
    lines = text.splitlines()
    last_line = lines[-1].strip() if lines else ""

    # Prose truncation check
    if len(last_line) >= 40 and last_char not in SENTENCE_TERMINATORS:
        findings.append(
            Finding(
                code="C3",
                start=max(0, len(text) - len(last_line)),
                end=len(text),
                kind="prose_unterminated_last_sentence",
                confidence=0.75,
                auto=False,  # Human decides on truncation
                note=f"last_char:{last_char}",
            )
        )
    return findings


@register_detector("C4")
def detect_c4(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect two joined documents (mid-doc BOM, abrupt copyright header, repeated title)."""
    findings: list[Finding] = []
    # Check for mid-document BOM (offset > 0)
    bom_idx = text.find("\ufeff", 1)
    if bom_idx != -1:
        findings.append(
            Finding(
                code="C4",
                start=bom_idx,
                end=bom_idx + 1,
                kind="mid_document_bom",
                confidence=0.9,
                auto=False,
                note="joined_doc_bom",
            )
        )

    # Check for mid-document Copyright / repeated title
    mid_copy = regex.search(r"(?i)\n\s*(Copyright\s+©|All\s+rights\s+reserved)", text[200:])
    if mid_copy:
        start, end = mid_copy.span()
        findings.append(
            Finding(
                code="C4",
                start=200 + start,
                end=200 + end,
                kind="mid_document_copyright",
                confidence=0.8,
                auto=False,
                note="possible_joined_doc",
            )
        )

    return findings


@register_detector("C5")
def detect_c5(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect SEO spam, keyword lists, tag clouds, or excessive URLs."""
    findings: list[Finding] = []

    # Check for explicit tag cloud or keyword lines
    raw_lines = text.splitlines()
    offset = 0
    for r_line in raw_lines:
        r_len = len(r_line)
        if TAG_CLOUD_LINE_RE.match(r_line):
            findings.append(
                Finding(
                    code="C5",
                    start=offset,
                    end=offset + r_len,
                    kind="tag_cloud",
                    confidence=0.9,
                    auto=False,
                    note="seo tag cloud",
                )
            )
        offset += r_len + 1

    lines = [line.strip() for line in raw_lines if line.strip()]
    if not lines:
        return findings

    # Check line delimiter patterns (1 to 4 tokens separated by , | · #)
    keyword_line_count = 0
    for line in lines:
        tokens = line.split()
        if 1 <= len(tokens) <= 4 and any(c in line for c in (",", "|", "·", "#")):
            keyword_line_count += 1

    ratio = keyword_line_count / len(lines)
    if ratio >= 0.60 and len(lines) >= 5:
        findings.append(
            Finding(
                code="C5",
                start=0,
                end=min(len(text), 100),
                kind="keyword_list_density",
                confidence=0.85,
                auto=False,
                note=f"keyword_line_ratio={ratio:.2f}",
            )
        )

    # Check URL token ratio
    tokens = text.split()
    if tokens:
        url_tokens = sum(
            1 for t in tokens if t.startswith("http://") or t.startswith("https://") or "www." in t
        )
        url_ratio = url_tokens / len(tokens)
        if url_ratio > 0.20:
            findings.append(
                Finding(
                    code="C5",
                    start=0,
                    end=min(len(text), 100),
                    kind="excessive_url_density",
                    confidence=0.9,
                    auto=False,
                    note=f"url_ratio={url_ratio:.2f}",
                )
            )

    return findings
