"""Input/output utilities, validation, and atomic writes.

Enforces Rule R5 (size guard), Rule R9 (privacy hygiene), and input schema validation.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


class ValidationError(Exception):
    """Raised when pack validation fails."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


def compute_file_sha256(path: str | Path) -> str:
    """Compute the SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_text_sha256(text: str) -> str:
    """Compute SHA-256 hash of UTF-8 encoded text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_pack(
    table: pa.Table,
    allow_large: bool = False,
) -> None:
    """Validate pack structure and constraints.

    Requirements:
    - Columns: doc_id, source, lang_label, text present.
    - Types: string / binary.
    - doc_id must be unique.
    - Size: 1 to 1000 rows (Rule R5 guard).
    """
    col_names = set(table.column_names)
    is_audit = (
        "clean_text" in col_names or "raw_text" in col_names or "applied_filters" in col_names
    )
    if is_audit:
        required_cols = {"doc_id", "source", "lang_label"}
    else:
        required_cols = {"doc_id", "source", "lang_label", "text"}
    missing = required_cols - col_names
    if missing:
        raise ValidationError(f"Missing required columns in pack: {sorted(missing)}")

    num_rows = table.num_rows
    if num_rows == 0:
        raise ValidationError("Pack is empty (0 rows)")

    # Rule R5: Hard guard against running on full corpus
    if num_rows > 1000 and not allow_large:
        raise ValidationError(
            f"Pack has {num_rows} rows (> 1000). Rule R5 violation: "
            "Never run medicines or tools on the full corpus without "
            "--i-know-this-is-not-the-full-corpus."
        )

    # Check doc_id uniqueness
    doc_ids = table["doc_id"].to_pylist()
    seen = set()
    duplicates: dict[str, int] = {}
    for did in doc_ids:
        if did in seen:
            duplicates[did] = duplicates.get(did, 1) + 1
        seen.add(did)

    if duplicates:
        # Per §3.3: list duplicate ids by count only, do not quote content
        dup_summary = ", ".join(f"'{k}' ({v} times)" for k, v in sorted(duplicates.items()))
        raise ValidationError(f"Duplicate doc_ids found in pack: {dup_summary}")


def load_pack(
    path: str | Path,
    allow_large: bool = False,
) -> tuple[pa.Table, list[dict[str, Any]], str]:
    """Load a Parquet pack, validate it, and return (table, pylist, file_sha256)."""
    p = Path(path)
    if not p.is_file():
        raise ValidationError(f"File not found: {path}")

    file_sha256 = compute_file_sha256(p)
    table = pq.read_table(p)
    validate_pack(table, allow_large=allow_large)
    records = table.to_pylist()
    return table, records, file_sha256


def atomic_write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically to path via a temporary file in the same directory."""
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = p.parent

    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding=encoding) as tf:
        tf.write(content)
        temp_name = tf.name

    os.replace(temp_name, p)


def atomic_write_json(path: str | Path, data: Any, indent: int = 2) -> None:
    """Write JSON data atomically."""
    content = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    atomic_write_text(path, content)


def atomic_write_parquet(path: str | Path, table: pa.Table, compression: str = "zstd") -> None:
    """Write a PyArrow Table atomically as Parquet."""
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = p.parent

    with tempfile.NamedTemporaryFile("wb", dir=temp_dir, delete=False, suffix=".parquet") as tf:
        temp_name = tf.name

    pq.write_table(table, temp_name, compression=compression, row_group_size=5000)
    os.replace(temp_name, p)
