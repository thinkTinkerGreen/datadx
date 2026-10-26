"""Tests for medicines (purity, idempotency, Hypothesis property tests).

Enforces Rule R3: ZWJ and ZWNJ survive strip_invisible.
Enforces Rule R4: Danda survives all medicines.
"""

import hypothesis.strategies as st
from hypothesis import given, settings

from datadx.medicine.base import DocCtx
from datadx.medicine.dedupe_lines import DedupeLinesMedicine
from datadx.medicine.join_split_matra import JoinSplitMatraMedicine
from datadx.medicine.registry import get_all_medicines
from datadx.medicine.strip_invisible import StripInvisibleMedicine

CTX = DocCtx(doc_id="test_doc", source="test", lang_label="mar_Deva")


def test_strip_invisible_preserves_zwnj_zwj():
    # Rule R3 check: ZWJ (\u200d) and ZWNJ (\u200c) must survive
    text = "मराठी\u200b मजकूर ZWNJ\u200c ZWJ\u200d"
    med = StripInvisibleMedicine()
    cleaned = med.apply(text, CTX)
    assert "\u200b" not in cleaned
    assert "\u200c" in cleaned  # ZWNJ preserved
    assert "\u200d" in cleaned  # ZWJ preserved


def test_danda_survives_all_medicines():
    # Rule R4 check: Danda (U+0964) and double danda (U+0965) preserved
    text = "हा स्वच्छ मजकूर आहे। यात पूर्णविराम आहे॥"
    for med in get_all_medicines():
        if med.action == "fix":
            cleaned = med.apply(text, CTX)
            assert "।" in cleaned
            assert "॥" in cleaned


def test_join_split_matra():
    text = "क िशोर आणि व िशाल"
    med = JoinSplitMatraMedicine()
    cleaned = med.apply(text, CTX)
    assert cleaned == "किशोर आणि विशाल"
    # Idempotency
    assert med.apply(cleaned, CTX) == cleaned


def test_dedupe_lines_idempotency():
    text = "Line A\nLine B\nLine A\nLine C"
    med = DedupeLinesMedicine()
    c1 = med.apply(text, CTX)
    assert c1 == "Line A\nLine B\nLine C"
    assert med.apply(c1, CTX) == c1


@settings(max_examples=50)
@given(st.text(min_size=0, max_size=500))
def test_medicines_idempotency_hypothesis(text: str):
    """Hypothesis property test: apply(apply(x)) == apply(x) for all fix medicines."""
    for med in get_all_medicines():
        if med.action == "fix":
            first_pass = med.apply(text, CTX)
            second_pass = med.apply(first_pass, CTX)
            assert first_pass == second_pass
