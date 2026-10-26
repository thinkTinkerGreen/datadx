"""Base protocol and context definition for medicines.

Medicines must be pure and idempotent: apply(apply(x)) == apply(x).
Enforces Rule R3 (preserve ZWJ/ZWNJ) and Rule R4 (NFC only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class DocCtx:
    """Document context passed to medicines (immutable)."""

    doc_id: str
    source: str
    lang_label: str
    row_index: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Medicine(Protocol):
    """Protocol that all medicines must implement."""

    code: str
    name: str
    action: Literal["fix", "drop"]

    def applies(self, text: str, ctx: DocCtx) -> bool:
        """Check if medicine applies to the given text and context."""
        ...

    def apply(self, text: str, ctx: DocCtx) -> str:
        """Apply medicine to text. Pure and idempotent."""
        ...
