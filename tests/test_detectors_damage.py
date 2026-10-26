"""Unit tests for Group G detectors (G1 to G4)."""

from datadx.detectors.damage import detect_g1, detect_g2
from datadx.policy import load_policy

POLICY = load_policy()


def test_g1_split_matra():
    # Base + space + matra (e.g. क िशोर)
    text = "येथे क िशोर अभ्यास करत आहे."
    findings = detect_g1(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "G1"
    assert "U+0915" in findings[0].hex_repr  # Base क
    assert "U+093F" in findings[0].hex_repr  # Matra िकर


def test_g1_mark_at_word_start():
    # Word starts with matra
    text = "हा शब्द िकर असा सुरू होतो."
    findings = detect_g1(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "G1"


def test_g2_misplaced_joiner():
    # Doubled joiners
    text = "येथे दुहेरी\u200c\u200c जॉइनर आहे."
    findings = detect_g2(text, {}, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "G2"
