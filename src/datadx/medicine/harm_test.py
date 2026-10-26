"""Harm test runner against gold standard sets.

Enforces Rule R8:
- Missing gold set -> harm_test=PENDING (never guesses).
- Fails if (n_changed + n_dropped) / n_gold > 1.0%.
- Evaluates raw byte changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import pyarrow.parquet as pq

from datadx.medicine.base import DocCtx, Medicine
from datadx.medicine.registry import get_all_medicines


@dataclass
class HarmTestResult:
    """Outcome of running a medicine on a gold set."""

    medicine_name: str
    code: str
    status: Literal["PASS", "FAIL", "PENDING"]
    n_gold: int
    n_changed: int
    n_dropped: int
    pct_impact: float
    changed_doc_ids: list[str] = field(default_factory=list)
    dropped_doc_ids: list[str] = field(default_factory=list)
    note: str = ""


def run_harm_test_single(
    medicine: Medicine,
    gold_records: list[dict[str, Any]],
    max_fail_pct: float = 1.0,
) -> HarmTestResult:
    """Run harm test for a single medicine on gold records."""
    n_gold = len(gold_records)
    if n_gold == 0:
        return HarmTestResult(
            medicine_name=medicine.name,
            code=medicine.code,
            status="PENDING",
            n_gold=0,
            n_changed=0,
            n_dropped=0,
            pct_impact=0.0,
            note="Empty gold set",
        )

    changed_ids: list[str] = []
    dropped_ids: list[str] = []

    for idx, doc in enumerate(gold_records):
        doc_id = str(doc.get("doc_id", f"gold_{idx}"))
        raw_text = str(doc.get("text", ""))
        raw_bytes = raw_text.encode("utf-8")

        ctx = DocCtx(
            doc_id=doc_id,
            source=str(doc.get("source", "")),
            lang_label=str(doc.get("lang_label", "")),
            row_index=idx,
        )

        if medicine.applies(raw_text, ctx):
            cleaned_text = medicine.apply(raw_text, ctx)
            cleaned_bytes = cleaned_text.encode("utf-8")

            if medicine.action == "drop" or (cleaned_text == "" and raw_text != ""):
                dropped_ids.append(doc_id)
            elif cleaned_bytes != raw_bytes:
                changed_ids.append(doc_id)

    n_changed = len(changed_ids)
    n_dropped = len(dropped_ids)
    # Disjoint union per prompt §9.3 and Rule R8
    pct_impact = 100.0 * (n_changed + n_dropped) / n_gold
    status: Literal["PASS", "FAIL", "PENDING"] = "FAIL" if pct_impact > max_fail_pct else "PASS"

    return HarmTestResult(
        medicine_name=medicine.name,
        code=medicine.code,
        status=status,
        n_gold=n_gold,
        n_changed=n_changed,
        n_dropped=n_dropped,
        pct_impact=pct_impact,
        changed_doc_ids=changed_ids,
        dropped_doc_ids=dropped_ids,
    )


def run_harm_tests(
    gold_path: str | Path | None,
    medicines: list[Medicine] | None = None,
    max_fail_pct: float = 1.0,
) -> list[HarmTestResult]:
    """Run harm tests across all medicines.

    If gold_path is None or missing, returns PENDING for all per Rule R8.
    """
    if medicines is None:
        medicines = get_all_medicines()

    if gold_path is None or not Path(gold_path).is_file():
        # Rule R8: Missing gold set = PENDING, never PASS
        return [
            HarmTestResult(
                medicine_name=m.name,
                code=m.code,
                status="PENDING",
                n_gold=0,
                n_changed=0,
                n_dropped=0,
                pct_impact=0.0,
                note="Gold set missing or not provided",
            )
            for m in medicines
        ]

    table = pq.read_table(gold_path)
    records = table.to_pylist()

    return [run_harm_test_single(m, records, max_fail_pct=max_fail_pct) for m in medicines]
