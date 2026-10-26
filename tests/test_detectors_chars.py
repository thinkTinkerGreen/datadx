"""Unit tests for Group A detectors (A1 to A6).

Enforces Rule R3: ZWJ and ZWNJ are NOT detected as A1 diseases.
Enforces Rule R4: NFC preserves danda and Indic text.
"""

from datadx.detectors.chars import detect_a1, detect_a2, detect_a3, detect_a4, detect_a5, detect_a6
from datadx.policy import load_policy

POLICY = load_policy()


def test_a1_positive_and_zwnj_zwj_exclusion():
    # ZWSP (\u200b) is A1. ZWNJ (\u200c) and ZWJ (\u200d) MUST NOT be A1 (Rule R3).
    text = "मराठी\u200bमजकूर ZWNJ\u200c ZWJ\u200d चाचणी"
    findings = detect_a1(text, {}, POLICY)
    codes = [f.code for f in findings]
    assert "A1" in codes
    assert len(findings) == 1
    assert findings[0].kind == "ZWSP"


def test_a1_bom_at_offset_zero():
    text = "\ufeffनमस्कार"
    findings = detect_a1(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].start == 0
    assert findings[0].kind == "BOM"


def test_a2_controls_and_crlf():
    text = "Line 1\r\nLine 2\x07Bell"
    findings = detect_a2(text, {}, POLICY)
    assert any(f.kind == "U+0007" for f in findings)
    assert any(f.kind == "CR" for f in findings)


def test_a3_mojibake_indic():
    text = "à¤®à¤°à¤¾à¤ à¥€"
    findings = detect_a3(text, {}, POLICY)
    assert len(findings) > 0
    assert findings[0].code == "A3"


def test_a4_replacement_character_count():
    text = "Error \ufffd and another \ufffd."
    findings = detect_a4(text, {}, POLICY)
    assert len(findings) == 2
    assert "fffd=2" in findings[0].note


def test_a5_nfc_exclusions_and_danda():
    # Danda (U+0964) should be untouched and not flag A5
    text = "हा स्वच्छ मजकूर आहे। यात दंडा आहे॥"
    findings = detect_a5(text, {}, POLICY)
    assert len(findings) == 0

    # 19 exclusions check: U+0958 (क़ QA)
    text_qa = "किताब \u0958 कलम"
    findings_qa = detect_a5(text_qa, {}, POLICY)
    assert len(findings_qa) > 0
    assert findings_qa[0].code == "A5"


def test_a6_mixed_script():
    # Intra-word mixed script: Marathi with Latin lookalike
    text = "हा शb्द मिश्रित आहे"  # 'b' in Devanagari word
    findings = detect_a6(text, {}, POLICY)
    assert len(findings) > 0
    assert findings[0].code == "A6"
