"""Unit tests for selectors.py across all selector forms and error paths."""

import argparse

import pytest

from datadx.selectors import SelectorError, parse_rows_spec, resolve

MOCK_DOCS = [
    {"doc_id": "doc_1", "text": "one"},
    {"doc_id": "doc_2", "text": "two"},
    {"doc_id": "doc_3", "text": "three"},
    {"doc_id": "doc_4", "text": "four"},
    {"doc_id": "doc_5", "text": "five"},
]


def test_resolve_row():
    args = argparse.Namespace(
        row=2,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=False,
        seed=1729,
    )
    assert resolve(MOCK_DOCS, args) == [1]


def test_resolve_row_out_of_range():
    args = argparse.Namespace(
        row=10,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=False,
        seed=1729,
    )
    with pytest.raises(SelectorError):
        resolve(MOCK_DOCS, args)


def test_resolve_doc_id():
    args = argparse.Namespace(
        row=None,
        doc_id="doc_3",
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=False,
        seed=1729,
    )
    assert resolve(MOCK_DOCS, args) == [2]


def test_resolve_doc_id_unknown():
    args = argparse.Namespace(
        row=None,
        doc_id="unknown_doc",
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=False,
        seed=1729,
    )
    with pytest.raises(SelectorError):
        resolve(MOCK_DOCS, args)


def test_parse_rows_spec():
    assert parse_rows_spec("1-3,5", 5) == [0, 1, 2, 4]


def test_parse_rows_spec_reversed_error():
    with pytest.raises(SelectorError, match="Reversed range"):
        parse_rows_spec("5-3", 5)


def test_resolve_sample_deterministic():
    args1 = argparse.Namespace(
        row=None,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=3,
        all=False,
        seed=1729,
    )
    args2 = argparse.Namespace(
        row=None,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=3,
        all=False,
        seed=1729,
    )
    assert resolve(MOCK_DOCS, args1) == resolve(MOCK_DOCS, args2)


def test_resolve_all():
    args = argparse.Namespace(
        row=None,
        doc_id=None,
        rows=None,
        doc_ids=None,
        ids_file=None,
        sample=None,
        all=True,
        seed=1729,
    )
    assert resolve(MOCK_DOCS, args) == [0, 1, 2, 3, 4]
