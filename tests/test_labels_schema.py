"""Tests for label sheet schema validation and rules."""

from pathlib import Path

from datadx.labels import LabelRow, validate_label_sheet, write_label_sheet


def test_validate_valid_label_sheet(tmp_path: Path):
    csv_file = tmp_path / "labels_test.csv"
    rows = [
        LabelRow("doc_1", "full", "clean", "", "", "", "Read and verified"),
        LabelRow(
            "doc_2",
            "partial",
            "fix",
            "A1;B1",
            "'test'@10 | '&amp;'@20",
            "U+200B@10",
            "Fix required",
        ),
    ]
    write_label_sheet(csv_file, rows)
    valid, errors = validate_label_sheet(csv_file, expected_doc_ids={"doc_1", "doc_2"})
    assert valid, f"Validation errors: {errors}"
    assert len(errors) == 0


def test_validate_invalid_clean_with_partial_read(tmp_path: Path):
    csv_file = tmp_path / "labels_invalid.csv"
    # Rule R1 violation: clean verdict with read=partial
    rows = [
        LabelRow("doc_1", "partial", "clean", "", "", "", "Not fully read"),
    ]
    write_label_sheet(csv_file, rows)
    valid, errors = validate_label_sheet(csv_file)
    assert not valid
    assert any("verdict is 'clean' but read is 'partial'" in e for e in errors)


def test_validate_f1_hex_must_be_empty(tmp_path: Path):
    csv_file = tmp_path / "labels_f1_hex.csv"
    # Rule R2 violation: hex filled for F1
    rows = [
        LabelRow("doc_1", "partial", "fix", "F1", "email at offset 10", "U+0040@10", "PII"),
    ]
    write_label_sheet(csv_file, rows)
    valid, errors = validate_label_sheet(csv_file)
    assert not valid
    assert any("hex must be empty for F1/E3" in e for e in errors)
