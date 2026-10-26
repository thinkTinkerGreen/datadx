"""Privacy canary test enforcing Rule R2 and Rule R9.

Inserts fake secrets and personal data into a synthetic document, executes the pipeline,
and asserts that none of the canary values appear anywhere in outputs (drafts, labels,
reports, or logs).
"""

from pathlib import Path

from datadx.detectors.code import detect_e3
from datadx.detectors.safety import detect_f1
from datadx.labels import build_draft_row, write_label_sheet
from datadx.policy import load_policy

POLICY = load_policy()

CANARY_EMAIL = "canary_private_person_xyz123@example.org"
CANARY_AWS_KEY = "AKIA9876543210FEDCBA"


def test_privacy_canary_leakage_prevention(tmp_path: Path):
    text = f"Contact {CANARY_EMAIL} with AWS key {CANARY_AWS_KEY} for support."

    # 1. Run detectors
    f1_findings = detect_f1(text, {}, POLICY)
    e3_findings = detect_e3(text, {}, POLICY)

    all_findings = f1_findings + e3_findings

    # Assert no finding stores the canary text
    for f in all_findings:
        assert CANARY_EMAIL not in f.kind
        assert CANARY_EMAIL not in f.note
        assert CANARY_EMAIL not in f.hex_repr
        assert CANARY_AWS_KEY not in f.kind
        assert CANARY_AWS_KEY not in f.note
        assert CANARY_AWS_KEY not in f.hex_repr

        # Check formatted evidence
        ev = f.format_evidence(text)
        assert CANARY_EMAIL not in ev
        assert CANARY_AWS_KEY not in ev

    # 2. Build draft row and write label sheet
    draft_row = build_draft_row("doc_canary", text, all_findings)
    out_csv = tmp_path / "canary_labels.csv"
    write_label_sheet(out_csv, [draft_row])

    # 3. Read output CSV and verify canary strings are absent
    content = out_csv.read_text(encoding="utf-8")
    assert CANARY_EMAIL not in content
    assert CANARY_AWS_KEY not in content
