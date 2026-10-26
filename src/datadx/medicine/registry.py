"""Registry for all implemented medicines."""

from __future__ import annotations

from datadx.medicine.base import Medicine
from datadx.medicine.dedupe_lines import DedupeLinesMedicine
from datadx.medicine.drop_exact_dupes import DropExactDupesMedicine
from datadx.medicine.drop_fffd import DropFffdMedicine
from datadx.medicine.fix_mojibake import FixMojibakeMedicine
from datadx.medicine.insert_script_boundary_whitespace import (
    InsertScriptBoundaryWhitespaceMedicine,
)
from datadx.medicine.join_split_matra import JoinSplitMatraMedicine
from datadx.medicine.nfc import NfcMedicine
from datadx.medicine.normalize_devanagari_punctuation import (
    NormalizeDevanagariPunctuationMedicine,
)
from datadx.medicine.remove_ghost_tokens import RemoveGhostTokensMedicine
from datadx.medicine.strip_controls import StripControlsMedicine
from datadx.medicine.strip_invisible import StripInvisibleMedicine
from datadx.medicine.strip_scraping_trailers import StripScrapingTrailersMedicine
from datadx.medicine.strip_tags import StripTagsMedicine
from datadx.medicine.unescape_entities import UnescapeEntitiesMedicine

_ALL_MEDICINES: list[Medicine] = [
    StripInvisibleMedicine(),
    StripControlsMedicine(),
    FixMojibakeMedicine(),
    DropFffdMedicine(),
    NfcMedicine(),
    InsertScriptBoundaryWhitespaceMedicine(),
    UnescapeEntitiesMedicine(),
    StripTagsMedicine(),
    RemoveGhostTokensMedicine(),
    StripScrapingTrailersMedicine(),
    DedupeLinesMedicine(),
    JoinSplitMatraMedicine(),
    NormalizeDevanagariPunctuationMedicine(),
    DropExactDupesMedicine(),
]

_MEDICINE_MAP: dict[str, Medicine] = {m.name: m for m in _ALL_MEDICINES}
_CODE_TO_MEDICINE: dict[str, Medicine] = {m.code: m for m in _ALL_MEDICINES}


def get_all_medicines() -> list[Medicine]:
    """Return all registered medicines in standard pipeline execution order."""
    return list(_ALL_MEDICINES)


def get_medicine_by_name(name: str) -> Medicine | None:
    return _MEDICINE_MAP.get(name)


def get_medicine_by_code(code: str) -> Medicine | None:
    return _CODE_TO_MEDICINE.get(code)
