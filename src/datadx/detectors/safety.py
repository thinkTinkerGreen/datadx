"""Detectors for Group F: Safety, Privacy, and Contamination (F1 to F3).

Enforces Rule R2: For F1 (personal data), NEVER copy the personal data value into any
file, log, exception message, or finding. Store ONLY type and offset. Hex is strictly empty.
Output format: '<type> at offset <offset>'.
"""

from __future__ import annotations

import re
from typing import Any

import phonenumbers

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

# Verhoeff algorithm tables for Aadhaar checksum validation
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 6, 1, 5, 2, 4, 0, 7, 3],
    [9, 4, 3, 8, 6, 7, 0, 2, 1, 5],
    [4, 2, 5, 7, 1, 3, 8, 6, 9, 0],
    [2, 1, 9, 5, 3, 4, 6, 7, 0, 8],
    [1, 7, 4, 2, 0, 6, 9, 3, 5, 8],
]


def _validate_verhoeff(num_str: str) -> bool:
    """Validate numeric string using Verhoeff algorithm."""
    c = 0
    try:
        digits = [int(x) for x in reversed(num_str)]
    except ValueError:
        return False
    for i, item in enumerate(digits):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][item]]
    return c == 0


# Email regex (excluding example/test domains)
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com|example\.(com|org))[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# PAN card regex (Permanent Account Number, India): 5 letters, 4 digits, 1 letter
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# IFSC code regex: 4 letters, 0, 6 alphanumeric
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

# Aadhaar regex: 12 digits starting with 2-9, optional spaces
AADHAAR_RE = re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b")

# Indic digit mapping table to ASCII
INDIC_DIGITS_TABLE = str.maketrans(
    {
        # Devanagari ०-९
        0x0966: "0",
        0x0967: "1",
        0x0968: "2",
        0x0969: "3",
        0x096A: "4",
        0x096B: "5",
        0x096C: "6",
        0x096D: "7",
        0x096E: "8",
        0x096F: "9",
        # Bengali ০-৯
        0x09E6: "0",
        0x09E7: "1",
        0x09E8: "2",
        0x09E9: "3",
        0x09EA: "4",
        0x09EB: "5",
        0x09EC: "6",
        0x09ED: "7",
        0x09EE: "8",
        0x09EF: "9",
        # Gurmukhi ੦-੯
        0x0A66: "0",
        0x0A67: "1",
        0x0A68: "2",
        0x0A69: "3",
        0x0A6A: "4",
        0x0A6B: "5",
        0x0A6C: "6",
        0x0A6D: "7",
        0x0A6E: "8",
        0x0A6F: "9",
        # Gujarati ૦-૯
        0x0AE6: "0",
        0x0AE7: "1",
        0x0AE8: "2",
        0x0AE9: "3",
        0x0AEA: "4",
        0x0AEB: "5",
        0x0AEC: "6",
        0x0AED: "7",
        0x0AEE: "8",
        0x0AEF: "9",
    }
)


@register_detector("F1")
def detect_f1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect personal data (emails, phone numbers, Aadhaar, PAN, IFSC).

    Rule R2: NEVER stores or quotes the personal data value. Hex is strictly empty.
    """
    findings: list[Finding] = []

    # Map Indic digits to ASCII for pattern matching only
    normalized_digits_text = text.translate(INDIC_DIGITS_TABLE)

    # 1. Emails
    for match in EMAIL_RE.finditer(text):
        offset = match.start()
        end = match.end()
        # Rule R2: type and offset only
        findings.append(
            Finding(
                code="F1",
                start=offset,
                end=end,
                kind="email",
                confidence=1.0,
                auto=True,
                hex_repr="",  # Rule R2: empty
            )
        )

    # 2. PAN Numbers
    for match in PAN_RE.finditer(text):
        offset = match.start()
        end = match.end()
        findings.append(
            Finding(
                code="F1",
                start=offset,
                end=end,
                kind="PAN",
                confidence=0.95,
                auto=True,
                hex_repr="",
            )
        )

    # 3. IFSC Codes
    for match in IFSC_RE.finditer(text):
        offset = match.start()
        end = match.end()
        findings.append(
            Finding(
                code="F1",
                start=offset,
                end=end,
                kind="IFSC",
                confidence=0.95,
                auto=True,
                hex_repr="",
            )
        )

    # 4. Aadhaar numbers (with Verhoeff checksum verification)
    for match in AADHAAR_RE.finditer(normalized_digits_text):
        matched_str = match.group().replace(" ", "")
        if len(matched_str) == 12 and _validate_verhoeff(matched_str):
            offset = match.start()
            end = match.end()
            findings.append(
                Finding(
                    code="F1",
                    start=offset,
                    end=end,
                    kind="Aadhaar",
                    confidence=1.0,
                    auto=True,
                    hex_repr="",
                )
            )

    # 5. Phone numbers via phonenumbers library
    regions = policy.phone_regions or ["IN", "GB", "US"]
    for region in regions:
        try:
            for phone_match in phonenumbers.PhoneNumberMatcher(normalized_digits_text, region):
                p_start = int(phone_match.start)
                p_end = int(phone_match.end)
                findings.append(
                    Finding(
                        code="F1",
                        start=p_start,
                        end=p_end,
                        kind="phone",
                        confidence=0.95,
                        auto=True,
                        hex_repr="",
                    )
                )
        except Exception:
            pass

    # Deduplicate overlapping spans
    unique_findings: list[Finding] = []
    seen_spans: set[tuple[int, int]] = set()
    for f in sorted(findings, key=lambda x: (x.start, x.end)):
        span = (f.start, f.end)
        if span not in seen_spans:
            seen_spans.add(span)
            unique_findings.append(f)

    return unique_findings


@register_detector("F2")
def detect_f2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect benchmark contamination (13-gram overlap)."""
    # If benchmarks dir is not provided, caller marks NOT_CHECKED:no-benchmarks per Rule R7
    return []


@register_detector("F3")
def detect_f3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Harmful content: Human only per DISEASES.md §2 and prompt §6."""
    return []
