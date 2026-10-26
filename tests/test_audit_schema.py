"""Tests for audit Parquet schema, provenance, and privacy separation."""

from pathlib import Path

import pyarrow.parquet as pq

from datadx.audit import generate_audit_record, write_audit_parquet


def test_audit_record_generation_and_byte_arithmetic():
    doc = {
        "doc_id": "test_doc_01",
        "source": "test_src",
        "lang_label": "mar_Deva",
        "text": "मराठी\u200b मजकूर",  # Contains A1 ZWSP (3 bytes in UTF-8)
    }
    rec = generate_audit_record(doc, 0)
    assert "strip_invisible" in rec["applied_filters"]
    assert rec["raw_text"] != rec["clean_text"]
    assert rec["bytes_removed"] == 3
    assert rec["chars_removed"] == 1


def test_audit_applied_filters_empty_iff_clean():
    clean_doc = {
        "doc_id": "clean_doc_02",
        "source": "test_src",
        "lang_label": "mar_Deva",
        "text": "हा पूर्णपणे स्वच्छ मजकूर आहे.",
    }
    rec = generate_audit_record(clean_doc, 1)
    assert len(rec["applied_filters"]) == 0
    assert rec["raw_text"] == rec["clean_text"]
    assert rec["bytes_removed"] == 0


def test_audit_parquet_roundtrip_and_public_sanitization(tmp_path: Path):
    doc = {
        "doc_id": "doc_roundtrip",
        "source": "test",
        "lang_label": "mar_Deva",
        "text": "मजकूर &amp; टॅग",
    }
    rec = generate_audit_record(doc, 0)
    out_file = tmp_path / "audit_test.parquet"

    priv_path, pub_path = write_audit_parquet([rec], out_file, write_public=True)
    assert priv_path.is_file()
    assert pub_path is not None and pub_path.is_file()

    # Read private audit parquet: contains raw_text and clean_text
    priv_table = pq.read_table(priv_path)
    assert "raw_text" in priv_table.column_names
    assert "clean_text" in priv_table.column_names

    # Read public audit parquet: text columns omitted per Rule R9
    pub_table = pq.read_table(pub_path)
    assert "raw_text" not in pub_table.column_names
    assert "clean_text" not in pub_table.column_names
    assert "applied_filters" in pub_table.column_names
    assert "bytes_removed" in pub_table.column_names
