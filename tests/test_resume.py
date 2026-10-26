"""Test resume functionality from run_state checkpoint."""

import json
from pathlib import Path

from datadx.io import atomic_write_json


def test_resume_state_integrity(tmp_path: Path):
    run_dir = tmp_path / "resume_test"
    run_dir.mkdir(parents=True, exist_ok=True)
    state_file = run_dir / "run_state.json"

    initial_state = {
        "pack_id": "test_pack",
        "last_batch": 5,
        "completed_rows": 125,
    }
    atomic_write_json(state_file, initial_state)

    # Resume read
    with open(state_file, encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["last_batch"] == 5
    assert loaded["completed_rows"] == 125
