"""Import all detector modules so their decorators register in the catalog."""

from datadx.detectors import (
    chars,
    code,
    damage,
    dups,
    lang,
    markup,
    safety,
    structure,
)

__all__ = [
    "chars",
    "code",
    "damage",
    "dups",
    "lang",
    "markup",
    "safety",
    "structure",
]
