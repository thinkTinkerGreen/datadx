"""Tests for GPU OOM adaptive batch halving and fallback logic."""

from datadx.gpu import run_with_oom_fallback


def test_oom_retry_and_halving():
    items = list(range(10))
    calls = []

    def mock_inference(batch):
        calls.append(len(batch))
        if len(batch) > 2:

            class OutOfMemoryError(Exception):
                pass

            raise OutOfMemoryError("CUDA out of memory")
        return [x * 2 for x in batch]

    results, meta = run_with_oom_fallback(
        mock_inference,
        items,
        initial_batch_size=8,
        max_retries=3,
    )

    assert len(results) == len(items)
    assert meta["retries"] > 0
    assert meta["final_batch_size"] <= 4
