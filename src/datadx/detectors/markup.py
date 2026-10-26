"""Detectors for Group B: Markup and Ghost Tokens (B1 to B5).

B3 is the highest-priority disease: every hit is reported even if the document is otherwise fine.
"""

from __future__ import annotations

import re
from typing import Any

from datadx.policy import Policy
from datadx.registry import Finding, register_detector

# B1: HTML entities
HTML_ENTITY_RE = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]{1,31}|#\d{1,7}|#[xX][0-9A-Fa-f]{1,6});")

# B2: HTML/XML tags
HTML_TAG_RE = re.compile(
    r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?/?>|<!--.*?-->",
    re.DOTALL,
)

# B3: Exact special tokens
EXACT_SPECIAL_TOKENS = [
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<|eot_id|>",
    "<|begin_of_text|>",
    "<|start_header_id|>",
    "<|end_header_id|>",
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "[INST]",
    "[/INST]",
    "<<SYS>>",
    "<</SYS>>",
    "<s>",
    "</s>",
    "<unk>",
    "<pad>",
    "<bos>",
    "<eos>",
    "<start_of_turn>",
    "<end_of_turn>",
    "<think>",
    "</think>",
    "[gMASK]",
    "[MASK]",
]

# B3 Regexes
B3_REGEXES = [
    re.compile(r"<\|[A-Za-z0-9_\- ▁]{1,40}\|>"),
    re.compile(r"<\uff5c[^\uff5c]{1,60}\uff5c>"),  # Full-width bars
    re.compile(r"<extra_id_\d+>"),
    re.compile(
        r"^#{2,3} ?(Assistant|Human|User|System|Instruction|Response):",
        re.MULTILINE | re.IGNORECASE,
    ),
]

# B4: Template and code junk patterns
TEMPLATE_RE = re.compile(r"\{\{[^{}\n]{1,100}\}\}|\$\{[^{}\n]{1,100}\}|\{%.*?%\}|\[object Object\]")
PROSE_CODE_JUNK_WORDS = re.compile(r"\b(undefined|NaN|null|None)\b")


@register_detector("B1")
def detect_b1(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect unescaped HTML entities in text."""
    findings: list[Finding] = []
    lang = str(ctx.get("lang_label", "")).lower()
    source = str(ctx.get("source", "")).lower()

    if any(m in lang for m in policy.markup_languages) and "code" in source:
        return findings

    for match in HTML_ENTITY_RE.finditer(text):
        start, end = match.span()
        findings.append(
            Finding(
                code="B1",
                start=start,
                end=end,
                kind=match.group(),
                confidence=1.0,
                auto=True,
            )
        )
    return findings


@register_detector("B2")
def detect_b2(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect HTML or XML tags in text (prose packs only)."""
    findings: list[Finding] = []
    lang = str(ctx.get("lang_label", "")).lower()
    source = str(ctx.get("source", "")).lower()

    if any(m in lang for m in policy.markup_languages) and "code" in source:
        return findings

    for match in HTML_TAG_RE.finditer(text):
        start, end = match.span()
        findings.append(
            Finding(
                code="B2",
                start=start,
                end=end,
                kind="html_tag",
                confidence=1.0,
                auto=True,
            )
        )
    return findings


@register_detector("B3")
def detect_b3(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect ghost chat markers and LLM special tokens (highest priority disease)."""
    findings: list[Finding] = []
    seen_spans: set[tuple[int, int]] = set()

    # Exact token search
    for token in EXACT_SPECIAL_TOKENS:
        start = 0
        while True:
            idx = text.find(token, start)
            if idx == -1:
                break
            span = (idx, idx + len(token))
            if span not in seen_spans:
                seen_spans.add(span)
                findings.append(
                    Finding(
                        code="B3",
                        start=idx,
                        end=idx + len(token),
                        kind=token,
                        confidence=1.0,
                        auto=True,
                    )
                )
            start = idx + 1

    # Regex search
    for pattern in B3_REGEXES:
        for match in pattern.finditer(text):
            span = match.span()
            if span not in seen_spans:
                seen_spans.add(span)
                findings.append(
                    Finding(
                        code="B3",
                        start=span[0],
                        end=span[1],
                        kind=match.group(),
                        confidence=1.0,
                        auto=True,
                    )
                )

    return sorted(findings, key=lambda f: f.start)


@register_detector("B4")
def detect_b4(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect template tags and JavaScript/Python code junk in prose packs."""
    findings: list[Finding] = []
    source = str(ctx.get("source", "")).lower()
    lang = str(ctx.get("lang_label", "")).lower()

    # Skip in code packs
    if "code" in source or "code" in lang:
        return findings

    for match in TEMPLATE_RE.finditer(text):
        start, end = match.span()
        findings.append(
            Finding(
                code="B4",
                start=start,
                end=end,
                kind="template_tag",
                confidence=1.0,
                auto=True,
            )
        )

    for match in PROSE_CODE_JUNK_WORDS.finditer(text):
        start, end = match.span()
        findings.append(
            Finding(
                code="B4",
                start=start,
                end=end,
                kind=match.group(),
                confidence=0.9,
                auto=True,
            )
        )

    return findings


@register_detector("B5")
def detect_b5(text: str, ctx: dict[str, Any], policy: Policy) -> list[Finding]:
    """Detect broken markdown (unclosed fences) and unbalanced LaTeX formulas."""
    findings: list[Finding] = []

    # 1. Unclosed markdown code fences
    fence_lines = [
        line
        for line in text.splitlines()
        if line.strip().startswith("```") or line.strip().startswith("~~~")
    ]
    if len(fence_lines) % 2 != 0:
        findings.append(
            Finding(
                code="B5",
                start=0,
                end=min(len(text), 40),
                kind="unclosed_code_fence",
                confidence=1.0,
                auto=True,
                note=f"fence_count={len(fence_lines)}",
            )
        )

    # 2. LaTeX brace balance on command blocks
    # Stack-based brace balance on \\[A-Za-z]+\{
    for match in re.finditer(r"\\[A-Za-z]+\{", text):
        start = match.start()
        brace_open = match.end() - 1
        stack = 1
        pos = brace_open + 1
        balanced = False
        while pos < len(text):
            if text[pos] == "{":
                stack += 1
            elif text[pos] == "}":
                stack -= 1
                if stack == 0:
                    balanced = True
                    break
            pos += 1
        if not balanced:
            findings.append(
                Finding(
                    code="B5",
                    start=start,
                    end=min(start + 20, len(text)),
                    kind="unclosed_latex_command_brace",
                    confidence=0.95,
                    auto=True,
                )
            )

    return findings
