"""Unit tests for Group C detectors (C1 to C5)."""

from datadx.detectors.structure import detect_c2, detect_c3, detect_c4, detect_c5
from datadx.policy import load_policy

POLICY = load_policy()


def test_c2_repeated_lines():
    text = "ओळ क्रमांक एक\nओळ क्रमांक एक\nओळ क्रमांक एक\nवेगळी ओळ"
    findings = detect_c2(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "C2"


def test_c3_truncated_document():
    # Long last line without terminal punctuation
    text = "हा एक परिच्छेद आहे.\nयेथे दस्तऐवज अचानक मध्येच संपतो आणि वाक्य अपूर्ण राहते"
    findings = detect_c3(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "C3"


def test_c3_clean_indic_danda():
    # Ends cleanly with Indic danda
    text = "हा एक परिच्छेद आहे.\nयेथे दस्तऐवज पूर्ण होतो आणि योग्य पूर्णविराम आहे।"
    findings = detect_c3(text, {}, POLICY)
    assert len(findings) == 0


def test_c4_mid_doc_bom():
    text = "पहिला भाग\n\ufeffदुसरा भाग"
    findings = detect_c4(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "C4"


def test_c5_keyword_list():
    text = "पुणे, मुंबई, नागपूर\nनाशिक | कोल्हापूर | सातारा\nऔरंगाबाद · सोलापूर · ठाणे\nजळगाव, धुळे, नांदेड\nसांगली | परभणी | बीड"
    findings = detect_c5(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "C5"
