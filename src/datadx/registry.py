"""Registry for disease codes, metadata, and findings.

Defines the core Finding structure and detector interfaces.
Enforces Rule R2: F1 and E3 store only type and offset, hex is always empty.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Finding:
    """A detected disease candidate in a document.

    Offsets are 0-based Unicode code point offsets into original text.
    For F1 (personal data) and E3 (secrets), kind is type-only, hex_repr is strictly empty,
    and the matched string is dropped immediately (Rule R2).
    """

    code: str
    start: int
    end: int
    kind: str
    confidence: float
    auto: bool
    borderline: bool = False
    note: str = ""
    hex_repr: str = ""

    def format_evidence(self, text: str) -> str:
        """Format evidence string conforming to DISEASES.md §3 / Prompt §8.

        Format: quote or description @offset.
        For F1 and E3: '<type> at offset <offset>' (never quotes text, Rule R2).
        """
        if self.code in ("F1", "E3"):
            return f"{self.kind} at offset {self.start}"

        # Safe substring extraction for other diseases
        snippet = text[self.start : self.end]
        if len(snippet) > 40:
            snippet = snippet[:37] + "..."
        # Redact any accidental emails or long tokens from snippets to enforce Rule R2
        snippet = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[email]", snippet)
        # Replace newlines in snippet for single-line evidence
        clean_snippet = snippet.replace("\n", "\\n").replace("\r", "\\r")
        return f"'{clean_snippet}'@{self.start}"


@dataclass(frozen=True)
class DiseaseMeta:
    """Metadata for a disease code."""

    code: str
    group: str
    name: str
    auto_detect: bool
    human_judgement_required: bool
    default_action: str  # "fix" or "drop"
    description: str


# Canonical registry of all disease codes (A1 to H3) per DISEASES.md
DISEASE_CATALOG: dict[str, DiseaseMeta] = {
    # Group A: Characters
    "A1": DiseaseMeta(
        "A1",
        "A",
        "Invisible junk characters",
        True,
        False,
        "fix",
        "zero-width space, BOM, bidi marks, soft hyphen",
    ),
    "A2": DiseaseMeta(
        "A2",
        "A",
        "Control characters",
        True,
        False,
        "fix",
        "U+0000-001F (except tab/newline), U+007F-009F",
    ),
    "A3": DiseaseMeta(
        "A3", "A", "Mojibake", True, False, "fix", "UTF-8 text decoded twice / broken encoding"
    ),
    "A4": DiseaseMeta(
        "A4", "A", "Replacement characters", True, False, "drop", "U+FFFD replacement characters"
    ),
    "A5": DiseaseMeta(
        "A5",
        "A",
        "Wrong normal form",
        True,
        True,
        "fix",
        "NFC normalization differences / nukta exclusions",
    ),
    "A6": DiseaseMeta(
        "A6", "A", "Wrong or mixed script", True, True, "fix", "Mixed script within word tokens"
    ),
    # Group B: Markup and ghost tokens
    "B1": DiseaseMeta(
        "B1",
        "B",
        "HTML entities",
        True,
        False,
        "fix",
        "&amp;, &nbsp;, numeric character references",
    ),
    "B2": DiseaseMeta(
        "B2", "B", "HTML or XML tags", True, False, "fix", "<div>, <br/>, tags in prose"
    ),
    "B3": DiseaseMeta(
        "B3",
        "B",
        "Ghost chat markers",
        True,
        False,
        "fix",
        "LLM chat tokens (<|im_start|>, [INST], <s>)",
    ),
    "B4": DiseaseMeta(
        "B4",
        "B",
        "Template and code junk in prose",
        True,
        False,
        "fix",
        "{{ var }}, ${...}, undefined, NaN",
    ),
    "B5": DiseaseMeta(
        "B5",
        "B",
        "Markdown or LaTeX broken",
        True,
        False,
        "fix",
        "Unclosed code fences, unbalanced LaTeX braces",
    ),
    # Group C: Structure
    "C1": DiseaseMeta(
        "C1", "C", "Boilerplate", False, True, "fix", "Menus, cookie banners, repeated footer links"
    ),
    "C2": DiseaseMeta(
        "C2",
        "C",
        "Repeated lines",
        True,
        False,
        "fix",
        "Identical line repeated >= 3 times or >= 30% of lines",
    ),
    "C3": DiseaseMeta(
        "C3",
        "C",
        "Truncated document",
        False,
        True,
        "drop",
        "Text stops in middle of sentence or code block",
    ),
    "C4": DiseaseMeta(
        "C4",
        "C",
        "Two documents joined",
        False,
        True,
        "drop",
        "Two unrelated texts joined with no boundary",
    ),
    "C5": DiseaseMeta(
        "C5",
        "C",
        "Lists of keywords or links",
        False,
        True,
        "drop",
        "SEO spam, tag clouds, link dumps",
    ),
    # Group D: Language
    "D1": DiseaseMeta(
        "D1",
        "D",
        "Wrong language label",
        True,
        True,
        "drop",
        "Language label disagrees with content",
    ),
    "D2": DiseaseMeta(
        "D2", "D", "Romanised Indic", True, False, "drop", "Indic language written in Latin letters"
    ),
    "D3": DiseaseMeta(
        "D3",
        "D",
        "Mixed language (code-mixing)",
        True,
        False,
        "fix",
        "Natural code-mixing (label only, not judged)",
    ),
    "D4": DiseaseMeta(
        "D4",
        "D",
        "Bad machine translation",
        False,
        True,
        "drop",
        "Broken MT, untranslated English, wrong grammar",
    ),
    "D5": DiseaseMeta(
        "D5", "D", "Translationese", False, True, "drop", "Unnatural translation style"
    ),
    # Group E: Code
    "E1": DiseaseMeta(
        "E1",
        "E",
        "Minified or generated code",
        True,
        False,
        "drop",
        "Very long lines, low alphanumeric share, @generated",
    ),
    "E2": DiseaseMeta(
        "E2", "E", "Data blobs", True, False, "drop", "Base64, hex dumps, numeric array literals"
    ),
    "E3": DiseaseMeta(
        "E3",
        "E",
        "Secrets",
        True,
        False,
        "drop",
        "API keys, private keys, passwords, high entropy tokens",
    ),
    "E4": DiseaseMeta(
        "E4", "E", "Repeated licence headers", True, False, "fix", "Repetitive license boilerplates"
    ),
    "E5": DiseaseMeta(
        "E5",
        "E",
        "Broken encoding in code",
        True,
        False,
        "fix",
        "Mojibake inside strings or comments",
    ),
    "E6": DiseaseMeta(
        "E6", "E", "Not code", False, True, "drop", "README, CSV, or log file mislabelled as code"
    ),
    # Group F: Safety, privacy, contamination
    "F1": DiseaseMeta(
        "F1", "F", "Personal data", True, True, "fix", "Emails, phones, Aadhaar, PAN, IFSC"
    ),
    "F2": DiseaseMeta(
        "F2",
        "F",
        "Benchmark leak",
        True,
        False,
        "drop",
        "13-gram overlap with benchmark evaluation sets",
    ),
    "F3": DiseaseMeta(
        "F3",
        "F",
        "Harmful content",
        False,
        True,
        "drop",
        "Human-evaluated harmful or dangerous content",
    ),
    # Group G: Earlier cleaning damage
    "G1": DiseaseMeta(
        "G1",
        "G",
        "Cut at vowel sign",
        True,
        False,
        "fix",
        "Whitespace preceding Indic dependent mark or split matra",
    ),
    "G2": DiseaseMeta(
        "G2", "G", "Lost ZWJ or ZWNJ", False, True, "fix", "Broken conjuncts or misplaced joiners"
    ),
    "G3": DiseaseMeta(
        "G3",
        "G",
        "Indic dropped by English rule",
        False,
        True,
        "drop",
        "Abrupt cuts, missing sections from aggressive cleaning",
    ),
    "G4": DiseaseMeta(
        "G4",
        "G",
        "Over-normalised",
        False,
        True,
        "fix",
        "NFKC digit conversion or character distortion",
    ),
    # Group H: Duplicates
    "H1": DiseaseMeta(
        "H1",
        "H",
        "Exact duplicate in pack",
        True,
        False,
        "drop",
        "Identical NFC-normalised text hash",
    ),
    "H2": DiseaseMeta(
        "H2",
        "H",
        "Near duplicate",
        True,
        False,
        "drop",
        "Character 5-gram Jaccard similarity >= 0.80",
    ),
    "H3": DiseaseMeta(
        "H3",
        "H",
        "Cross-lingual duplicate",
        False,
        True,
        "drop",
        "Cross-source/lingual duplicate from reference index",
    ),
}


DetectorFunc = Callable[[str, dict[str, Any], Any], list[Finding]]

_DETECTOR_REGISTRY: dict[str, DetectorFunc] = {}


def register_detector(code: str) -> Callable[[DetectorFunc], DetectorFunc]:
    """Decorator to register a detector function for a disease code."""

    def decorator(fn: DetectorFunc) -> DetectorFunc:
        _DETECTOR_REGISTRY[code] = fn
        return fn

    return decorator


def get_detector(code: str) -> DetectorFunc | None:
    """Retrieve the registered detector function for a disease code."""
    return _DETECTOR_REGISTRY.get(code)


def get_all_detectors() -> dict[str, DetectorFunc]:
    """Retrieve all registered detector functions."""
    return dict(_DETECTOR_REGISTRY)
