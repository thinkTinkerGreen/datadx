"""Tests for verdict rule precedence and Rule R1 enforcement."""

from datadx.labels import build_draft_row
from datadx.registry import Finding


def test_rule_r1_clean_impossible_in_draft():
    # When no diseases are found, draft row MUST NOT be verdict=clean or read=full
    row = build_draft_row("doc_clean", "स्वच्छ मजकूर", [])
    assert row.read == "partial"  # Rule R1: never full automatically
    assert row.status == "clean_candidate"
    assert row.verdict != "clean"  # Rule R1: tool never writes clean on its own


def test_verdict_precedence_f3_over_fix():
    f_b1 = Finding(code="B1", start=0, end=5, kind="&amp;", confidence=1.0, auto=True)
    f_f3 = Finding(code="F3", start=10, end=20, kind="harmful", confidence=1.0, auto=False)
    row = build_draft_row("doc_1", "text", [f_b1, f_f3])
    assert row.verdict == "drop"


def test_verdict_precedence_e3_drops():
    f_e3 = Finding(code="E3", start=0, end=20, kind="AWS key", confidence=1.0, auto=True)
    row = build_draft_row("doc_2", "text", [f_e3])
    assert row.verdict == "drop"


def test_verdict_f1_count_threshold():
    # < 3 F1 -> fix
    f1_single = [Finding(code="F1", start=0, end=10, kind="email", confidence=1.0, auto=True)]
    row_fix = build_draft_row("doc_3", "text", f1_single)
    assert row_fix.verdict == "fix"

    # >= 3 F1 -> drop
    f1_triple = [
        Finding(code="F1", start=0, end=10, kind="email", confidence=1.0, auto=True),
        Finding(code="F1", start=15, end=25, kind="phone", confidence=1.0, auto=True),
        Finding(code="F1", start=30, end=40, kind="PAN", confidence=1.0, auto=True),
    ]
    row_drop = build_draft_row("doc_4", "text", f1_triple)
    assert row_drop.verdict == "drop"
