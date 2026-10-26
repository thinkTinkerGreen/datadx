"""Audit Parquet generation with complete provenance tracking.

Enforces Rule R9:
- Audit Parquet files contain raw text and are PRIVATE ARTIFACTS.
- Never committed to git. Stored only in private storage or Google Drive.
- Generates optional public audit file with raw_text and clean_text omitted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa

from datadx.io import atomic_write_parquet, compute_text_sha256
from datadx.medicine.base import DocCtx, Medicine
from datadx.medicine.registry import get_all_medicines

# PyArrow schema for private audit Parquet
AUDIT_SCHEMA = pa.schema(
    [
        ("doc_id", pa.string()),
        ("source", pa.string()),
        ("lang_label", pa.string()),
        ("raw_text", pa.string()),
        ("clean_text", pa.string()),
        ("applied_filters", pa.list_(pa.string())),
        ("bytes_removed", pa.int64()),
        ("bytes_delta", pa.int64()),
        ("chars_removed", pa.int64()),
        ("diseases", pa.list_(pa.string())),
        ("verdict", pa.string()),
        ("dropped", pa.bool_()),
        ("raw_sha256", pa.string()),
        ("clean_sha256", pa.string()),
        ("pipeline_version", pa.string()),
    ]
)

# PyArrow schema for public audit Parquet (omits text fields)
PUBLIC_AUDIT_SCHEMA = pa.schema(
    [
        ("doc_id", pa.string()),
        ("source", pa.string()),
        ("lang_label", pa.string()),
        ("applied_filters", pa.list_(pa.string())),
        ("bytes_removed", pa.int64()),
        ("bytes_delta", pa.int64()),
        ("chars_removed", pa.int64()),
        ("diseases", pa.list_(pa.string())),
        ("verdict", pa.string()),
        ("dropped", pa.bool_()),
        ("raw_sha256", pa.string()),
        ("clean_sha256", pa.string()),
        ("pipeline_version", pa.string()),
    ]
)


def apply_medicines_to_document(
    raw_text: str,
    ctx: DocCtx,
    medicines: list[Medicine] | None = None,
) -> tuple[str, list[str], bool]:
    """Apply a sequential stack of medicines to raw text.

    Returns: (clean_text, applied_filters, dropped)
    """
    if medicines is None:
        medicines = get_all_medicines()

    current_text = raw_text
    applied_filters: list[str] = []
    dropped = False

    for med in medicines:
        if med.applies(current_text, ctx):
            next_text = med.apply(current_text, ctx)
            if med.action == "drop" or (next_text == "" and current_text != ""):
                applied_filters.append(med.name)
                current_text = ""
                dropped = True
                break
            elif next_text != current_text:
                applied_filters.append(med.name)
                current_text = next_text

    return current_text, applied_filters, dropped


def generate_audit_record(
    doc: dict[str, Any],
    row_index: int,
    confirmed_labels: dict[str, Any] | None = None,
    pipeline_version: str = "0.1.0",
    medicines: list[Medicine] | None = None,
) -> dict[str, Any]:
    """Generate a single audit record for a document."""
    doc_id = str(doc["doc_id"])
    source = str(doc.get("source", ""))
    lang_label = str(doc.get("lang_label", ""))
    raw_text = str(doc.get("text", ""))

    ctx = DocCtx(
        doc_id=doc_id,
        source=source,
        lang_label=lang_label,
        row_index=row_index,
    )

    # Provenance labels from confirmed label sheet if available
    label_info = confirmed_labels.get(doc_id, {}) if confirmed_labels else {}
    verdict = label_info.get("verdict", "unlabelled")
    diseases_str = label_info.get("diseases", "")
    diseases = [d.strip() for d in diseases_str.split(";") if d.strip()]

    # If confirmed clean, Rule R1: document found to have no disease, clean_text is raw_text
    applied_filters: list[str] = []
    if verdict == "clean":
        clean_text = raw_text
        dropped = False
    else:
        clean_text, applied_filters, dropped = apply_medicines_to_document(
            raw_text, ctx, medicines=medicines
        )

    raw_bytes = raw_text.encode("utf-8")
    clean_bytes = clean_text.encode("utf-8")

    bytes_delta = len(raw_bytes) - len(clean_bytes)
    bytes_removed = max(0, bytes_delta)
    chars_removed = len(raw_text) - len(clean_text)

    return {
        "doc_id": doc_id,
        "source": source,
        "lang_label": lang_label,
        "raw_text": raw_text,
        "clean_text": clean_text,
        "applied_filters": applied_filters,
        "bytes_removed": bytes_removed,
        "bytes_delta": bytes_delta,
        "chars_removed": chars_removed,
        "diseases": diseases,
        "verdict": verdict,
        "dropped": dropped,
        "raw_sha256": compute_text_sha256(raw_text),
        "clean_sha256": compute_text_sha256(clean_text),
        "pipeline_version": pipeline_version,
    }


def write_audit_parquet(
    records: list[dict[str, Any]],
    out_path: str | Path,
    write_public: bool = True,
) -> tuple[Path, Path | None]:
    """Write private audit Parquet and optional public sanitized Parquet."""
    out_p = Path(out_path).resolve()
    table = pa.Table.from_pylist(records, schema=AUDIT_SCHEMA)
    atomic_write_parquet(out_p, table)

    public_p: Path | None = None
    if write_public:
        public_records = [
            {k: v for k, v in r.items() if k not in ("raw_text", "clean_text")} for r in records
        ]
        public_table = pa.Table.from_pylist(public_records, schema=PUBLIC_AUDIT_SCHEMA)
        public_p = out_p.parent / f"audit_public_{out_p.stem.replace('audit_', '')}.parquet"
        atomic_write_parquet(public_p, public_table)

    return out_p, public_p
