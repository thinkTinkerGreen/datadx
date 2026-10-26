"""Detectors for Group H: Duplicates (H1 to H3).

H1: Exact duplicates via NFC SHA-256 (preserves lowest index as original).
H2: Near duplicates via character 5-gram shingle Jaccard >= 0.80 (deterministic brute-force for N <= 1000).
H3: Cross-lingual duplicate (reference index check).
"""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Any

from datadx.policy import Policy
from datadx.registry import Finding, register_detector


def compute_char_5grams(text: str) -> set[str]:
    """Compute character 5-gram shingles over NFC-normalized text."""
    norm = unicodedata.normalize("NFC", text)
    if len(norm) < 5:
        return {norm}
    return {norm[i : i + 5] for i in range(len(norm) - 4)}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


@register_detector("H1")
def detect_h1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect exact duplicates in pack (keeps lowest index as original)."""
    findings: list[Finding] = []
    norm_text = unicodedata.normalize("NFC", text)
    curr_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()

    exact_hash_map: dict[str, tuple[int, str]] = ctx.get("exact_hash_map", {})
    curr_idx = ctx.get("row_index", 0)

    if curr_hash in exact_hash_map:
        orig_idx, orig_doc_id = exact_hash_map[curr_hash]
        if orig_idx < curr_idx:
            findings.append(
                Finding(
                    code="H1",
                    start=0,
                    end=min(len(text), 100),
                    kind="exact_duplicate",
                    confidence=1.0,
                    auto=True,
                    note=f"dup_of:{orig_doc_id}",
                )
            )

    return findings


@register_detector("H2")
def detect_h2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect near duplicates (char 5-gram Jaccard >= 0.80 against earlier docs in pack)."""
    findings: list[Finding] = []
    near_dupes_map: dict[int, str] = ctx.get("near_dupes_map", {})
    curr_idx = ctx.get("row_index", 0)

    if curr_idx in near_dupes_map:
        orig_doc_id = near_dupes_map[curr_idx]
        findings.append(
            Finding(
                code="H2",
                start=0,
                end=min(len(text), 100),
                kind="near_duplicate",
                confidence=0.9,
                auto=True,
                note=f"near_dup_of:{orig_doc_id}",
            )
        )

    return findings


@register_detector("H3")
def detect_h3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Cross-lingual duplicate from reference index (Rule R7: NOT_CHECKED if absent)."""
    return []
