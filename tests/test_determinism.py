"""Determinism test enforcing Rule R10.

Executes the pipeline twice on the synthetic pack and asserts byte-identical outputs.
"""

import argparse
import hashlib
from pathlib import Path

import pytest

from datadx.cli import cmd_scan


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_determinism_contract(tmp_path: Path):
    fixture_pack = Path("tests/fixtures/synthetic_pack.parquet")
    if not fixture_pack.is_file():
        pytest.skip("Synthetic fixture pack not found")

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    args1 = argparse.Namespace(
        pack=str(fixture_pack),
        pack_id="synthetic",
        out=str(out1),
        policy=None,
        reads="mr",
        i_know_this_is_not_the_full_corpus=True,
        row=None,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=True,
        seed=1729,
    )
    args2 = argparse.Namespace(
        pack=str(fixture_pack),
        pack_id="synthetic",
        out=str(out2),
        policy=None,
        reads="mr",
        i_know_this_is_not_the_full_corpus=True,
        row=None,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=True,
        seed=1729,
    )

    cmd_scan(args1)
    cmd_scan(args2)

    draft1 = out1 / "labels_draft.csv"
    draft2 = out2 / "labels_draft.csv"

    assert draft1.is_file() and draft2.is_file()
    assert _hash_file(draft1) == _hash_file(draft2), (
        "Draft CSV content hash differs between identical runs!"
    )
