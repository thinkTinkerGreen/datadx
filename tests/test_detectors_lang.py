"""Unit tests for Group D detectors (D1 to D5)."""

from datadx.detectors.lang import detect_d1, detect_d2, detect_d3
from datadx.policy import load_policy

POLICY = load_policy()


def test_d1_script_discrepancy():
    # Label is Marathi but content is purely English
    ctx = {"lang_label": "mar_Deva"}
    text = "This document is entirely written in English without a single Devanagari character."
    findings = detect_d1(text, ctx, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "D1"


def test_d2_romanised_indic():
    # Romanised Indic: Latin letters >= 60% in Indic pack
    ctx = {"lang_label": "mar_Deva"}
    text = "Namaskar mitranno, kase aahat tumhi sarvjan? Aajcha divas khup chhan aahe."
    findings = detect_d2(text, ctx, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "D2"


def test_d3_code_mixed():
    # Code-mixing in sentence
    ctx = {"lang_label": "mar_Deva"}
    text = "मी आज office मध्ये meeting attend केली आणि नंतर project submit केला."
    findings = detect_d3(text, ctx, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "D3"
    assert findings[0].note == "code-mixed"
