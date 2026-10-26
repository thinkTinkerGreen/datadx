"""Unit tests for Group B detectors (B1 to B5)."""

from datadx.detectors.markup import detect_b1, detect_b2, detect_b3, detect_b4, detect_b5
from datadx.policy import load_policy

POLICY = load_policy()


def test_b1_html_entities():
    text = "किंमत &amp; दर &nbsp; 100"
    findings = detect_b1(text, {}, POLICY)
    assert len(findings) == 2
    assert findings[0].code == "B1"


def test_b2_html_tags():
    text = "<div>मराठी परिच्छेद</div><br/>"
    findings = detect_b2(text, {}, POLICY)
    assert len(findings) > 0
    assert findings[0].code == "B2"


def test_b3_ghost_tokens():
    text = "<|im_start|>system\nतू एक हुशार सहाय्यक आहेस.<|im_end|>\n[INST] प्रश्न [/INST]"
    findings = detect_b3(text, {}, POLICY)
    assert len(findings) >= 3
    assert all(f.code == "B3" for f in findings)


def test_b4_template_junk():
    text = "वापरकर्ता {{ user_name }} आणि [object Object]"
    findings = detect_b4(text, {}, POLICY)
    assert len(findings) == 2
    assert all(f.code == "B4" for f in findings)


def test_b5_broken_fence():
    text = "```python\nprint('hello')\n"
    findings = detect_b5(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "B5"
