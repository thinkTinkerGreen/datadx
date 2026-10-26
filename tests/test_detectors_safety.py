"""Unit tests for Group F detectors (F1 to F3).

Enforces Rule R2: For F1 (personal data), never stores personal data values.
Output evidence format is '<type> at offset <offset>'.
"""

from datadx.detectors.safety import detect_f1
from datadx.policy import load_policy

POLICY = load_policy()


def test_f1_email_privacy():
    text = "संपर्क: user_test_secret@example.org वर करा."
    findings = detect_f1(text, {}, POLICY)
    assert len(findings) == 1
    f = findings[0]
    assert f.code == "F1"
    assert f.kind == "email"
    assert f.hex_repr == ""  # Rule R2: hex is empty

    ev = f.format_evidence(text)
    assert ev == f"email at offset {f.start}"
    assert "user_test_secret" not in ev


def test_f1_pan_card():
    text = "पॅन कार्ड: ABCDE1234F आहे."
    findings = detect_f1(text, {}, POLICY)
    assert any(f.kind == "PAN" for f in findings)


def test_f1_ifsc_code():
    text = "बँक IFSC कोड: SBIN0123456 आहे."
    findings = detect_f1(text, {}, POLICY)
    assert any(f.kind == "IFSC" for f in findings)
