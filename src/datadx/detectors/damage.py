"""Detectors for Group G: Earlier Cleaning Damage (G1 to G4) - critical for Indic.

Enforces Rule R3: ZWJ/ZWNJ are never removed. G2 candidates are human-confirmed.
"""

from __future__ import annotations

from typing import Any

import regex

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

# Indic dependent marks (matras, viramas, anusvara, visarga) in major Indic blocks
INDIC_MARKS_RE = regex.compile(
    r"[\u0901-\u0903\u093a-\u094f\u0951-\u0957\u0962\u0963"  # Devanagari
    r"\u0981-\u0983\u09bc\u09be-\u09cd\u09d7\u09e2\u09e3"  # Bengali
    r"\u0a01-\u0a03\u0a3c\u0a3e-\u0a4d\u0a70\u0a71\u0a75"  # Gurmukhi
    r"\u0a81-\u0a83\u0abc\u0abe-\u0acd\u0ae2\u0ae3"  # Gujarati
    r"\u0b01-\u0b03\u0b3c\u0b3e-\u0b4d\u0b56\u0b57\u0b62\u0b63"  # Odia
    r"\u0b82\u0bbe-\u0bcd\u0bd7"  # Tamil
    r"\u0c00-\u0c03\u0c3e-\u0c4d\u0c55\u0c56\u0c62\u0c63"  # Telugu
    r"\u0c81-\u0c83\u0cbc\u0cbe-\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3"  # Kannada
    r"\u0d00-\u0d03\u0d3b\u0d3c\u0d3e-\u0d4d\u0d57\u0d62\u0d63]"  # Malayalam
)

# G1 regex: Whitespace directly followed by an Indic dependent mark, or base + space + mark
G1_SPLIT_MATRA_RE = regex.compile(
    r"([\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}])\s+("
    r"[\u0901-\u0903\u093a-\u094f\u0951-\u0957\u0962\u0963"
    r"\u0981-\u0983\u09bc\u09be-\u09cd\u09d7\u09e2\u09e3"
    r"\u0a01-\u0a03\u0a3c\u0a3e-\u0a4d\u0a70\u0a71\u0a75"
    r"\u0a81-\u0a83\u0abc\u0abe-\u0acd\u0ae2\u0ae3"
    r"\u0b01-\u0b03\u0b3c\u0b3e-\u0b4d\u0b56\u0b57\u0b62\u0b63"
    r"\u0b82\u0bbe-\u0bcd\u0bd7"
    r"\u0c00-\u0c03\u0c3e-\u0c4d\u0c55\u0c56\u0c62\u0c63"
    r"\u0c81-\u0c83\u0cbc\u0cbe-\u0ccd\u0cd5\u0cd6\u0ce2\u0ce3"
    r"\u0d00-\u0d03\u0d3b\u0d3c\u0d3e-\u0d4d\u0d57\u0d62\u0d63])"
)

# Corrupted clock time with Visarga (e.g. ९ ः ३० or ९ः३०)
G1_SPLIT_VISARGA_RE = regex.compile(r"([\u0966-\u096F0-9])\s*ः\s*([\u0966-\u096F0-9])")

# ASCII pipe used as sentence terminator / danda in Indic text
G4_PIPE_AS_DANDA_RE = regex.compile(
    r"(?<=[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}\p{M}])\s*\|\s*(?=[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}\s]|$)"
)

# Indic virama code points
VIRAMAS = {"\u094d", "\u09cd", "\u0a4d", "\u0acd", "\u0b4d", "\u0bcd", "\u0c4d", "\u0ccd", "\u0d4d"}


@register_detector("G1")
def detect_g1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect cut at vowel sign (whitespace between base consonant and dependent matra)."""
    findings: list[Finding] = []

    # 1. Base + space + mark pattern (e.g. 'क ि')
    for match in G1_SPLIT_MATRA_RE.finditer(text):
        start, end = match.span()
        base_ch = match.group(1)
        mark_ch = match.group(2)
        hex_repr = f"U+{ord(base_ch):04X}@{start},U+{ord(mark_ch):04X}@{end - 1}"
        findings.append(
            Finding(
                code="G1",
                start=start,
                end=end,
                kind="split_matra",
                confidence=1.0,
                auto=True,
                note="split matra",
                hex_repr=hex_repr,
            )
        )

    # 2. Corrupted time with Visarga (e.g. '९ ः ३०')
    for match in G1_SPLIT_VISARGA_RE.finditer(text):
        start, end = match.span()
        findings.append(
            Finding(
                code="G1",
                start=start,
                end=end,
                kind="split_visarga",
                confidence=1.0,
                auto=True,
                note="split visarga",
                hex_repr=f"U+0903@{start}",
            )
        )

    # 3. Word starting with an Indic dependent mark
    word_start_matches = regex.finditer(r"(?<=^|\s)" + INDIC_MARKS_RE.pattern, text)
    for match in word_start_matches:
        start = match.start()
        end = match.end()
        ch = text[start]
        findings.append(
            Finding(
                code="G1",
                start=start,
                end=end,
                kind="mark_at_word_start",
                confidence=1.0,
                auto=True,
                note="dangling vowel sign",
                hex_repr=f"U+{ord(ch):04X}@{start}",
            )
        )

    return findings


@register_detector("G2")
def detect_g2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect misplaced or lost joiners (ZWJ/ZWNJ at word boundary or doubled).

    Candidate only: tool NEVER repairs G2 automatically (prompt §6 Group G2).
    """
    findings: list[Finding] = []

    # Check doubled joiners or word-edge joiners
    joiner_matches = regex.finditer(
        r"[\u200c\u200d]{2,}|(?<=^|\s)[\u200c\u200d]|[\u200c\u200d](?=$|\s)", text
    )
    for match in joiner_matches:
        start, end = match.span()
        ch = text[start]
        findings.append(
            Finding(
                code="G2",
                start=start,
                end=end,
                kind="misplaced_joiner",
                confidence=0.8,
                auto=False,  # Human judgement required
                hex_repr=f"U+{ord(ch):04X}@{start}",
            )
        )

    return findings


@register_detector("G3")
def detect_g3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Indic dropped by English rule: Human only per DISEASES.md §2."""
    return []


@register_detector("G4")
def detect_g4(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect over-normalised or distorted characters (e.g. ASCII pipe used as danda)."""
    findings: list[Finding] = []
    lines = text.splitlines()
    offset = 0
    for line in lines:
        line_len = len(line)
        # Skip markdown table rows (starts and ends with |)
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            offset += line_len + 1
            continue
        for match in G4_PIPE_AS_DANDA_RE.finditer(line):
            start = offset + match.start()
            end = offset + match.end()
            findings.append(
                Finding(
                    code="G4",
                    start=start,
                    end=end,
                    kind="ascii_pipe_as_danda",
                    confidence=0.85,
                    auto=False,
                    note="ascii pipe as danda",
                    hex_repr=f"U+007C@{start}",
                )
            )
            if len(findings) >= 3:
                break
        offset += line_len + 1
        if len(findings) >= 3:
            break
    return findings
