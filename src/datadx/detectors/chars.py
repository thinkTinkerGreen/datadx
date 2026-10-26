"""Detectors for Group A: Characters (A1 to A6).

Implements deterministic detection for invisible characters, controls, mojibake,
replacement characters, normal form, and mixed script.
Enforces Rule R3 (never remove ZWJ/ZWNJ), Rule R4 (NFC only).
"""

from __future__ import annotations

import unicodedata
from typing import Any

import ftfy
import regex

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

# A1 sets
# Banned / disease invisible characters
A1_CHARS = {
    "\u200b": "ZWSP",
    "\ufeff": "BOM",
    "\u00ad": "SHY",
    "\u202a": "LRE",
    "\u202b": "RLE",
    "\u202c": "PDF",
    "\u202d": "LRO",
    "\u202e": "RLO",
    "\u2066": "LRI",
    "\u2067": "RLI",
    "\u2068": "FSI",
    "\u2069": "PDI",
}

# Report only set (human decides)
A1_EXTRA_CHARS = {
    "\u200e": "LRM",
    "\u200f": "RLM",
    "\u2060": "WJ",
    "\u061c": "ALM",
    "\u180e": "MVS",
}

# 19 Unicode NFC composition exclusion code points (base + nukta)
NFC_EXCLUSIONS_19 = {
    0x0958,
    0x0959,
    0x095A,
    0x095B,
    0x095C,
    0x095D,
    0x095E,
    0x095F,  # Devanagari
    0x09DC,
    0x09DD,
    0x09DF,  # Bengali
    0x0A33,
    0x0A36,
    0x0A59,
    0x0A5A,
    0x0A5B,
    0x0A5E,  # Gurmukhi
    0x0B5C,
    0x0B5D,  # Odia
}

# Mojibake patterns for Indic UTF-8 double-decoding
MOJIBAKE_INDIC_RE = regex.compile(
    r"à[\u00a4-\u00b7\u20ac\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178\x80-\x9f]"
    r"|â€|Ã[\x80-\xbf]|Â[\x80-\xbf]"
)

# Indic script Unicode block regex
INDIC_LETTER_RE = regex.compile(
    r"[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}\p{Sinhala}]"
)


def _is_indic_char(ch: str) -> bool:
    cp = ord(ch)
    # Check major Indic blocks
    return (
        (0x0900 <= cp <= 0x097F)  # Devanagari
        or (0x0980 <= cp <= 0x09FF)  # Bengali / Assamese
        or (0x0A00 <= cp <= 0x0A7F)  # Gurmukhi
        or (0x0A80 <= cp <= 0x0AFF)  # Gujarati
        or (0x0B00 <= cp <= 0x0B7F)  # Odia
        or (0x0B80 <= cp <= 0x0BFF)  # Tamil
        or (0x0C00 <= cp <= 0x0C7F)  # Telugu
        or (0x0C80 <= cp <= 0x0CFF)  # Kannada
        or (0x0D00 <= cp <= 0x0D7F)  # Malayalam
        or (0x0D80 <= cp <= 0x0DFF)  # Sinhala
    )


@register_detector("A1")
def detect_a1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect invisible junk characters. Never flags ZWJ (U+200D) or ZWNJ (U+200C)."""
    findings: list[Finding] = []
    for idx, ch in enumerate(text):
        if ch in A1_CHARS:
            name = A1_CHARS[ch]
            hex_str = f"U+{ord(ch):04X}@{idx}"
            findings.append(
                Finding(
                    code="A1",
                    start=idx,
                    end=idx + 1,
                    kind=name,
                    confidence=1.0,
                    auto=True,
                    hex_repr=hex_str,
                )
            )
        elif ch in A1_EXTRA_CHARS:
            name = A1_EXTRA_CHARS[ch]
            hex_str = f"U+{ord(ch):04X}@{idx}"
            findings.append(
                Finding(
                    code="A1",
                    start=idx,
                    end=idx + 1,
                    kind="extra",
                    confidence=0.8,
                    auto=False,  # Human decides on extra format characters
                    note=f"report_only:{name}",
                    hex_repr=hex_str,
                )
            )
    return findings


@register_detector("A2")
def detect_a2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect control characters (U+0000-001F except tab and newline, U+007F-009F, and CR)."""
    findings: list[Finding] = []
    # Check if all CRs are CRLF
    all_crlf = True
    cr_indices: list[int] = []

    for idx, ch in enumerate(text):
        cp = ord(ch)
        if ch == "\r":
            cr_indices.append(idx)
            if idx + 1 >= len(text) or text[idx + 1] != "\n":
                all_crlf = False
        elif (0 <= cp <= 0x1F and ch not in ("\t", "\n")) or (0x7F <= cp <= 0x9F):
            hex_str = f"U+{cp:04X}@{idx}"
            findings.append(
                Finding(
                    code="A2",
                    start=idx,
                    end=idx + 1,
                    kind=f"U+{cp:04X}",
                    confidence=1.0,
                    auto=True,
                    hex_repr=hex_str,
                )
            )

    if cr_indices:
        note = "CRLF-only" if all_crlf else "bare-CR"
        for idx in cr_indices:
            findings.append(
                Finding(
                    code="A2",
                    start=idx,
                    end=idx + 1,
                    kind="CR",
                    confidence=1.0,
                    auto=True,
                    note=note,
                    hex_repr=f"U+000D@{idx}",
                )
            )

    return findings


@register_detector("A3")
def detect_a3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect mojibake (double UTF-8 decoding or corrupted encodings)."""
    findings: list[Finding] = []

    # 1. Regex search for known mojibake signatures
    for match in MOJIBAKE_INDIC_RE.finditer(text):
        start, end = match.span()
        sub = text[start:end]
        hex_parts = [f"U+{ord(c):04X}@{start + i}" for i, c in enumerate(sub)]
        findings.append(
            Finding(
                code="A3",
                start=start,
                end=end,
                kind="mojibake_signature",
                confidence=0.95,
                auto=True,
                hex_repr=",".join(hex_parts[:3]),
            )
        )

    # 2. ftfy check: if ftfy fixes text and increases Indic letter share
    fixed = ftfy.fix_encoding(text)
    if fixed != text and not findings:
        orig_indic = sum(1 for c in text if _is_indic_char(c))
        fixed_indic = sum(1 for c in fixed if _is_indic_char(c))
        if fixed_indic > orig_indic:
            # Emit candidate finding for ftfy repair
            findings.append(
                Finding(
                    code="A3",
                    start=0,
                    end=min(len(text), 50),
                    kind="ftfy_fixable_mojibake",
                    confidence=0.9,
                    auto=True,
                    note=f"indic_gain:{fixed_indic - orig_indic}",
                )
            )

    return findings


@register_detector("A4")
def detect_a4(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect U+FFFD replacement characters and count them."""
    findings: list[Finding] = []
    fffd_indices = [i for i, ch in enumerate(text) if ch == "\ufffd"]
    count = len(fffd_indices)

    if count > 0:
        for idx in fffd_indices:
            findings.append(
                Finding(
                    code="A4",
                    start=idx,
                    end=idx + 1,
                    kind="U+FFFD",
                    confidence=1.0,
                    auto=True,
                    note=f"fffd={count}",
                    hex_repr=f"U+FFFD@{idx}",
                )
            )
    return findings


@register_detector("A5")
def detect_a5(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect non-NFC normalized text and report 19 composition exclusion code points."""
    findings: list[Finding] = []

    # Check the 19 exclusion code points (which NFC splits into base + nukta)
    for idx, ch in enumerate(text):
        cp = ord(ch)
        if cp in NFC_EXCLUSIONS_19:
            findings.append(
                Finding(
                    code="A5",
                    start=idx,
                    end=idx + 1,
                    kind="nfc_exclusion_code_point",
                    confidence=1.0,
                    auto=False,  # Judgement on look vs meaning is human
                    note="byte-only",
                    hex_repr=f"U+{cp:04X}@{idx}",
                )
            )

    # Check overall NFC equality
    nfc_text = unicodedata.normalize("NFC", text)
    if nfc_text != text and not findings:
        # Grapheme diff
        orig_clusters = regex.findall(r"\X", text)
        offset = 0
        for _i, cluster in enumerate(orig_clusters):
            c_len = len(cluster)
            norm_cluster = unicodedata.normalize("NFC", cluster)
            if norm_cluster != cluster:
                hex_parts = [f"U+{ord(c):04X}@{offset + j}" for j, c in enumerate(cluster)]
                findings.append(
                    Finding(
                        code="A5",
                        start=offset,
                        end=offset + c_len,
                        kind="non_nfc_grapheme",
                        confidence=1.0,
                        auto=False,
                        note="byte-only",
                        hex_repr=",".join(hex_parts),
                    )
                )
            offset += c_len

    return findings


@register_detector("A6")
def detect_a6(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect wrong or mixed script within word tokens."""
    findings: list[Finding] = []

    # Word-level mixed script check (Devanagari/Bengali letters mixed with Latin/Greek)
    words = regex.finditer(r"\b[\p{L}\p{M}]+\b", text)
    for w in words:
        word = w.group()
        start, end = w.span()
        has_indic = bool(INDIC_LETTER_RE.search(word))
        has_latin = bool(regex.search(r"[\p{Latin}\p{Cyrillic}\p{Greek}]", word))
        if has_indic and has_latin:
            is_agglutinated = bool(
                regex.search(r"(\p{Latin}\p{Devanagari}|\p{Devanagari}\p{Latin})", word)
            )
            note = "script agglutination" if is_agglutinated else f"token:{word}"
            findings.append(
                Finding(
                    code="A6",
                    start=start,
                    end=end,
                    kind="script_agglutination" if is_agglutinated else "mixed_script_token",
                    confidence=0.85,
                    auto=False,  # Human judgement required
                    note=note[:190],
                )
            )

    # Assamese vs Bengali script discrepancy
    lang = str(ctx.get("lang_label", "")).lower()
    if "as" in lang or "asm" in lang:
        # Assamese requires Ra (U+09F0) or Wa (U+09F1)
        has_as_specific = "\u09f0" in text or "\u09f1" in text
        if not has_as_specific and len(text) > 200:
            findings.append(
                Finding(
                    code="A6",
                    start=0,
                    end=min(len(text), 50),
                    kind="assamese_lacks_ra_wa",
                    confidence=0.7,
                    auto=False,
                    note="candidate_bengali_confusion",
                )
            )

    return findings
