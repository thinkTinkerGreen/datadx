"""Label sheet generation, confirmation, and validation.

Enforces Rule R1:
- Tool NEVER writes verdict=clean or read=full on its own.
- Writes clean_candidate into draft file.
- Only an explicit human confirm action promotes to verdict=clean and read=full.
Enforces Rule R2:
- Never copies PII (F1) or secret (E3) values into labels.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

from datadx.registry import DISEASE_CATALOG, Finding

# Expected CSV columns per labels_TEMPLATE.csv
LABEL_COLUMNS = ["doc_id", "read", "verdict", "diseases", "evidence", "hex", "note"]
DRAFT_COLUMNS = LABEL_COLUMNS + ["status"]

F1_E3_EVIDENCE_RE = re.compile(r"^[a-z0-9 _-]+ at offset \d+$", re.IGNORECASE)


@dataclass
class LabelRow:
    """A row in the diagnosis label sheet."""

    doc_id: str
    read: str  # "full" or "partial"
    verdict: str  # "clean", "fix", or "drop"
    diseases: str  # ";"-separated sorted codes
    evidence: str
    hex: str
    note: str
    status: str = "auto"

    def to_dict(self, include_status: bool = False) -> dict[str, str]:
        res = {
            "doc_id": self.doc_id,
            "read": self.read,
            "verdict": self.verdict,
            "diseases": self.diseases,
            "evidence": self.evidence,
            "hex": self.hex,
            "note": self.note,
        }
        if include_status:
            res["status"] = self.status
        return res


def build_draft_row(
    doc_id: str,
    text: str,
    findings: list[Finding],
    default_read: str = "partial",
) -> LabelRow:
    """Construct a draft label row from findings.

    Adheres strictly to Rule R1: Never outputs verdict=clean or read=full.
    """
    if not text.strip():
        # Empty document
        return LabelRow(
            doc_id=doc_id,
            read="partial",
            verdict="drop",
            diseases="",
            evidence="",
            hex="",
            note="empty text",
            status="needs_human",
        )

    if not findings:
        # Candidate clean - requires human confirmation
        return LabelRow(
            doc_id=doc_id,
            read="partial",  # R1: never full automatically
            verdict="fix",  # Temporary draft placeholder; marked clean_candidate in status
            diseases="",
            evidence="",
            hex="",
            note="candidate clean - pending human confirmation",
            status="clean_candidate",
        )

    # Sort diseases ascending
    unique_codes = sorted({f.code for f in findings})
    diseases_str = ";".join(unique_codes)

    # Format evidence and hex
    evidence_parts: list[str] = []
    hex_parts: list[str] = []
    has_human_only = False

    for f in findings:
        evidence_parts.append(f.format_evidence(text))
        if f.hex_repr and f.code in ("A1", "A2", "A3", "A4", "A5", "G1", "G2"):
            hex_parts.append(f.hex_repr)
        if not f.auto or f.borderline:
            has_human_only = True

    evidence_str = " | ".join(evidence_parts[:10])  # Cap at 10 items for readability
    hex_str = ",".join(hex_parts[:10])

    # Precedence verdict calculation (§7)
    codes_set = set(unique_codes)
    verdict = "fix"

    if "F3" in codes_set or "F2" in codes_set or "E3" in codes_set:
        verdict = "drop"
    elif "F1" in codes_set:
        f1_count = sum(1 for f in findings if f.code == "F1")
        verdict = "drop" if f1_count >= 3 else "fix"
    elif any(c in codes_set for c in ("A4", "G3", "H1", "E6", "D1")):
        verdict = "drop"

    status = "needs_human" if has_human_only else "auto"

    return LabelRow(
        doc_id=doc_id,
        read="partial",  # R1: draft rows never have read=full
        verdict=verdict,
        diseases=diseases_str,
        evidence=evidence_str,
        hex=hex_str,
        note="",
        status=status,
    )


def validate_label_sheet(
    csv_path: str | Path,
    expected_doc_ids: set[str] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a final label sheet against all criteria in prompt §8 and DISEASES.md §3."""
    errors: list[str] = []
    p = Path(csv_path)
    if not p.is_file():
        return False, [f"File not found: {csv_path}"]

    with open(p, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != LABEL_COLUMNS:
            errors.append(f"Header mismatch. Expected: {LABEL_COLUMNS}, Got: {reader.fieldnames}")
            return False, errors

        seen_ids: set[str] = set()

        for idx, row in enumerate(reader, start=2):
            doc_id = row.get("doc_id", "")
            read = row.get("read", "")
            verdict = row.get("verdict", "")
            diseases_str = row.get("diseases", "")
            evidence = row.get("evidence", "")
            hex_val = row.get("hex", "")
            note = row.get("note", "")

            # 1. doc_id uniqueness
            if not doc_id:
                errors.append(f"Row {idx}: missing doc_id")
            elif doc_id in seen_ids:
                errors.append(f"Row {idx}: duplicate doc_id '{doc_id}'")
            seen_ids.add(doc_id)

            if expected_doc_ids and doc_id not in expected_doc_ids:
                errors.append(f"Row {idx}: doc_id '{doc_id}' not in pack")

            # 2. read and verdict enum
            if read not in ("full", "partial"):
                errors.append(f"Row {idx}: invalid read '{read}' (must be 'full' or 'partial')")
            if verdict not in ("clean", "fix", "drop"):
                errors.append(
                    f"Row {idx}: invalid verdict '{verdict}' (must be 'clean', 'fix', or 'drop')"
                )

            # 3. diseases codes
            codes = [c.strip() for c in diseases_str.split(";") if c.strip()]
            for code in codes:
                if code not in DISEASE_CATALOG:
                    errors.append(f"Row {idx}: unknown disease code '{code}'")
            if codes != sorted(codes):
                errors.append(f"Row {idx}: disease codes not sorted ascending: '{diseases_str}'")

            # 4. clean verdict consistency
            if verdict == "clean":
                if diseases_str:
                    errors.append(
                        f"Row {idx}: verdict is 'clean' but diseases is not empty: '{diseases_str}'"
                    )
                if read != "full":
                    errors.append(
                        f"Row {idx}: verdict is 'clean' but read is '{read}' (Rule R1: must be 'full')"
                    )
            elif verdict in ("fix", "drop") and not diseases_str and note != "empty text":
                errors.append(f"Row {idx}: verdict is '{verdict}' but diseases is empty")

            # 5. evidence format and privacy check (F1/E3)
            if "F1" in codes or "E3" in codes:
                if hex_val:
                    errors.append(f"Row {idx}: hex must be empty for F1/E3 per Rule R2")
                ev_items = [item.strip() for item in evidence.split(" | ") if item.strip()]
                has_f1_e3 = any(F1_E3_EVIDENCE_RE.match(item) for item in ev_items)
                if not has_f1_e3:
                    errors.append(
                        f"Row {idx}: F1/E3 specified in diseases but missing '<type> at offset <offset>' evidence"
                    )
                for item in ev_items:
                    # Non-quoted items representing F1/E3 findings must follow type at offset
                    if (
                        not (item.startswith("'") or item.startswith('"'))
                        and any(
                            t in item.lower()
                            for t in [
                                "email",
                                "phone",
                                "aadhaar",
                                "pan",
                                "ifsc",
                                "key",
                                "token",
                                "secret",
                            ]
                        )
                        and not F1_E3_EVIDENCE_RE.match(item)
                    ):
                        errors.append(
                            f"Row {idx}: F1/E3 evidence '{item}' does not match type + offset pattern"
                        )

            # 6. note constraints
            if "\n" in note or "\r" in note:
                errors.append(f"Row {idx}: note contains newline")
            if len(note) > 200:
                errors.append(f"Row {idx}: note exceeds 200 characters ({len(note)})")

    return len(errors) == 0, errors


def write_label_sheet(path: str | Path, rows: list[LabelRow], include_status: bool = False) -> None:
    """Write label rows to CSV atomically."""
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = DRAFT_COLUMNS if include_status else LABEL_COLUMNS

    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row.to_dict(include_status=include_status))

    # Atomic write
    from datadx.io import atomic_write_text

    atomic_write_text(p, output.getvalue())
