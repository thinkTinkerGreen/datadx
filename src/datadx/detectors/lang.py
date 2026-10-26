"""Detectors for Group D: Language (D1 to D5).

Enforces Rule R6: D4 and D5 are human-only and never judged automatically.
"""

from __future__ import annotations

import unicodedata
from typing import Any

import regex

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

INDIC_LANGS = {
    "hi",
    "hin",
    "mar",
    "mr",
    "bn",
    "ben",
    "as",
    "asm",
    "gu",
    "guj",
    "pa",
    "pan",
    "or",
    "ori",
    "ta",
    "tam",
    "te",
    "tel",
    "kn",
    "kan",
    "ml",
    "mal",
    "sa",
    "san",
    "ne",
    "nep",
    "mai",
    "doi",
    "brx",
    "kok",
}

INDIC_SCRIPT_RE = regex.compile(
    r"[\p{Devanagari}\p{Bengali}\p{Gurmukhi}\p{Gujarati}\p{Oriya}\p{Tamil}\p{Telugu}\p{Kannada}\p{Malayalam}]"
)
LATIN_LETTER_RE = regex.compile(r"\p{Latin}")


def _is_indic_pack(lang_label: str) -> bool:
    label = lang_label.lower().split("_")[0]
    return label in INDIC_LANGS or any(lang in label for lang in INDIC_LANGS)


@register_detector("D1")
def detect_d1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect candidate wrong language label.

    Closely related languages (hi/mr/ne, as/bn) are always human-only candidates.
    """
    findings: list[Finding] = []
    lang_label = str(ctx.get("lang_label", "")).lower()

    # Script-level discrepancy: doc labelled Indic but has zero Indic characters
    indic_letters = len(INDIC_SCRIPT_RE.findall(text))
    latin_letters = len(LATIN_LETTER_RE.findall(text))

    if _is_indic_pack(lang_label) and len(text) > 100 and indic_letters == 0 and latin_letters > 20:
        findings.append(
            Finding(
                code="D1",
                start=0,
                end=min(len(text), 100),
                kind="discrepant_script_for_lang",
                confidence=0.85,
                auto=False,  # Closely related / script checks require human judgement
                note=f"indic_count={indic_letters};latin_count={latin_letters}",
            )
        )

    return findings


@register_detector("D2")
def detect_d2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect Romanised Indic (Latin letters >= 60% of letters in Indic pack)."""
    findings: list[Finding] = []
    lang_label = str(ctx.get("lang_label", "")).lower()

    if not _is_indic_pack(lang_label):
        return findings

    letters = [ch for ch in text if unicodedata.category(ch).startswith("L")]
    if not letters or len(letters) < 30:
        return findings

    latin_count = sum(1 for ch in letters if "LATIN" in unicodedata.name(ch, ""))
    ratio = latin_count / len(letters)

    threshold = policy.get_threshold("d2_latin_letter_ratio", 0.60)
    band = policy.borderline_band

    if ratio >= (threshold - band):
        is_borderline = abs(ratio - threshold) <= band
        findings.append(
            Finding(
                code="D2",
                start=0,
                end=min(len(text), 100),
                kind="romanised_indic",
                confidence=min(1.0, ratio),
                auto=not is_borderline,
                borderline=is_borderline,
                note=f"latin_ratio={ratio:.2f}",
            )
        )

    return findings


@register_detector("D3")
def detect_d3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect code-mixed text (Latin token share per sentence between 5% and 95%).

    Per DISEASES.md §2 and Prompt §6:
    Evaluated per sentence; note says `code-mixed`; never judged.
    """
    findings: list[Finding] = []
    lang_label = str(ctx.get("lang_label", "")).lower()

    if not _is_indic_pack(lang_label):
        return findings

    # Iterate over sentences with exact offsets using sentence delimiters (\n, ।, ॥, ., !, ?)
    sentence_matches = regex.finditer(r"[^\n।॥.!?]+", text)
    for m in sentence_matches:
        sentence = m.group()
        words = regex.findall(r"\b[\p{L}\p{M}]+\b", sentence)
        latin_words = sum(1 for w in words if regex.search(r"^\p{Latin}+$", w))
        indic_words = sum(1 for w in words if INDIC_SCRIPT_RE.search(w))

        total = latin_words + indic_words
        if total >= 2 and latin_words >= 1 and indic_words >= 1:
            latin_share = latin_words / total
            if 0.05 <= latin_share <= 0.95:
                findings.append(
                    Finding(
                        code="D3",
                        start=m.start(),
                        end=m.end(),
                        kind="code_mixed",
                        confidence=0.9,
                        auto=True,
                        note="code-mixed",
                    )
                )
                if len(findings) >= 3:
                    break

    return findings


@register_detector("D4")
def detect_d4(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Bad machine translation: human-only (Rule R6)."""
    # No automatic detector per prompt §6 and Rule R6
    return []


@register_detector("D5")
def detect_d5(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Translationese: human-only (Rule R6)."""
    # No automatic detector per prompt §6 and Rule R6
    return []
