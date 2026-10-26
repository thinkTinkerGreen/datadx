"""Unit tests for Group H detectors (H1 to H3)."""

from datadx.detectors.dups import compute_char_5grams, detect_h1, detect_h2, jaccard_similarity
from datadx.policy import load_policy

POLICY = load_policy()


def test_h1_exact_duplicate():
    text = "हा एक समान मजकूर आहे."
    import hashlib

    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # First occurrence at row 0 (original), second at row 1 (duplicate)
    ctx = {
        "row_index": 1,
        "exact_hash_map": {h: (0, "doc_0")},
    }
    findings = detect_h1(text, ctx, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "H1"
    assert "dup_of:doc_0" in findings[0].note


def test_h2_near_duplicate_jaccard():
    t1 = "हा एक मोठा मराठी मजकूर आहे जो चाचणीसाठी वापरला जातो."
    t2 = "हा एक मोठा मराठी मजकूर आहे जो चाचणीसाठी वापरला जातो!!"
    s1 = compute_char_5grams(t1)
    s2 = compute_char_5grams(t2)
    jaccard = jaccard_similarity(s1, s2)
    assert jaccard >= 0.80

    ctx = {
        "row_index": 1,
        "near_dupes_map": {1: "doc_0"},
    }
    findings = detect_h2(t2, ctx, POLICY)
    assert len(findings) == 1
    assert findings[0].code == "H2"
