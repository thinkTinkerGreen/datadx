"""Document selection interface for data diagnosis.

Resolves selectors (--row, --doc-id, --rows, --doc-ids, --ids-file, --sample, --all)
into sorted, deduplicated, 0-based row indices.
"""

from __future__ import annotations

import argparse
import random
from typing import Any


class SelectorError(Exception):
    """Raised when selector arguments are invalid."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


def add_selector_arguments(parser: argparse.ArgumentParser) -> None:
    """Add standard mutually exclusive selector flags to an argument parser."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--row",
        type=int,
        help="One row index (1-based, matching viewer's [i/total]).",
    )
    group.add_argument(
        "--doc-id",
        type=str,
        help="One document ID.",
    )
    group.add_argument(
        "--rows",
        type=str,
        help="Comma-separated rows/ranges (1-based, e.g. 1-25,40,100-120).",
    )
    group.add_argument(
        "--doc-ids",
        type=str,
        help="Comma-separated list of document IDs.",
    )
    group.add_argument(
        "--ids-file",
        type=str,
        help="Path to file containing document IDs (one per line).",
    )
    group.add_argument(
        "--sample",
        type=int,
        help="Deterministic random sample size.",
    )
    group.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Select whole pack (default).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1729,
        help="Random seed for sampling (default: 1729).",
    )


def parse_rows_spec(spec: str, total_rows: int) -> list[int]:
    """Parse a rows specification string into 0-based indices.

    Format: comma-separated list of single numbers or ranges (e.g. '1-25,40,100-120').
    Numbers and ranges are 1-based and inclusive.
    """
    if not spec.strip():
        raise SelectorError("Empty --rows specification")

    indices: set[int] = set()
    parts = spec.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            tokens = part.split("-")
            if len(tokens) != 2:
                raise SelectorError(f"Invalid range token: {part}")
            try:
                start = int(tokens[0].strip())
                end = int(tokens[1].strip())
            except ValueError:
                raise SelectorError(f"Non-integer range token: {part}") from None

            if start > end:
                raise SelectorError(f"Reversed range: {part}")
            if start < 1:
                raise SelectorError(f"Out-of-range row index (must be >= 1): {start}")
            if end > total_rows:
                raise SelectorError(f"Out-of-range row index (max {total_rows}): {end}")

            for r in range(start, end + 1):
                indices.add(r - 1)
        else:
            try:
                row = int(part)
            except ValueError:
                raise SelectorError(f"Non-integer row token: {part}") from None

            if row < 1:
                raise SelectorError(f"Out-of-range row index (must be >= 1): {row}")
            if row > total_rows:
                raise SelectorError(f"Out-of-range row index (max {total_rows}): {row}")
            indices.add(row - 1)

    return sorted(indices)


def resolve(
    docs: Any,
    args: argparse.Namespace | dict[str, Any],
) -> list[int]:
    """Resolve selection arguments against documents.

    Returns a sorted, deduplicated list of 0-based row indices.
    """
    if hasattr(docs, "num_rows"):
        total_rows = int(docs.num_rows)
        doc_ids: list[str] = [str(x) for x in docs["doc_id"].to_pylist()]
    else:
        total_rows = len(docs)
        doc_ids = [str(d["doc_id"]) for d in docs]

    if total_rows == 0:
        return []

    # Get argument values
    def get_arg(name: str, default: Any = None) -> Any:
        if isinstance(args, argparse.Namespace):
            return getattr(args, name, default)
        return args.get(name, default)

    row = get_arg("row")
    doc_id = get_arg("doc_id")
    rows_spec = get_arg("rows")
    doc_ids_spec = get_arg("doc_ids")
    ids_file = get_arg("ids_file")
    sample = get_arg("sample")
    seed = get_arg("seed", 1729)

    doc_id_to_idx: dict[str, int] = {did: idx for idx, did in enumerate(doc_ids)}

    if row is not None:
        if row < 1 or row > total_rows:
            raise SelectorError(f"Row {row} out of range [1, {total_rows}]")
        return [row - 1]

    if doc_id is not None:
        if doc_id not in doc_id_to_idx:
            raise SelectorError(f"Unknown doc_id: {doc_id}")
        return [doc_id_to_idx[doc_id]]

    if rows_spec is not None:
        return parse_rows_spec(rows_spec, total_rows)

    if doc_ids_spec is not None:
        target_ids = [tid.strip() for tid in doc_ids_spec.split(",") if tid.strip()]
        result: list[int] = []
        for tid in target_ids:
            if tid not in doc_id_to_idx:
                raise SelectorError(f"Unknown doc_id in --doc-ids: {tid}")
            result.append(doc_id_to_idx[tid])
        return sorted(set(result))

    if ids_file is not None:
        try:
            with open(ids_file, encoding="utf-8") as f:
                target_ids = [line.strip() for line in f if line.strip()]
        except OSError as e:
            raise SelectorError(f"Cannot read ids-file: {e}") from e

        result = []
        for tid in target_ids:
            if tid not in doc_id_to_idx:
                raise SelectorError(f"Unknown doc_id in ids-file: {tid}")
            result.append(doc_id_to_idx[tid])
        return sorted(set(result))

    if sample is not None:
        if sample <= 0:
            raise SelectorError(f"Sample size must be > 0: {sample}")
        if sample > total_rows:
            raise SelectorError(f"Sample size {sample} exceeds total rows {total_rows}")
        # Deterministic sample over sorted doc_ids
        rng = random.Random(seed)
        selected_ids = rng.sample(sorted(doc_ids), sample)
        return sorted(doc_id_to_idx[did] for did in selected_ids)

    # Default is --all
    return list(range(total_rows))
