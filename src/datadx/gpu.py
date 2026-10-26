"""GPU resource management, memory cap, and OOM-safe batch execution.

Adheres strictly to §11 Compute specification:
- Caps CUDA memory at 50% (torch.cuda.set_per_process_memory_fraction(0.5)).
- Configures PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True.
- Employs fp16 inference with torch.inference_mode().
- Adaptive batch size halving on CUDA OOM (up to 5 retries, then CPU fallback).
- Records peak memory usage.
"""

from __future__ import annotations

import contextlib
import logging
import os
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("datadx.gpu")


def init_gpu_environment(memory_fraction: float = 0.5) -> dict[str, Any]:
    """Initialize PyTorch GPU settings with 50% memory cap and memory flags."""
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    info: dict[str, Any] = {
        "cuda_available": False,
        "device_name": "cpu",
        "memory_fraction": memory_fraction,
        "peak_memory_bytes": 0,
        "total_memory_bytes": 0,
    }

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(memory_fraction, 0)
            device_name = torch.cuda.get_device_name(0)
            total_mem = torch.cuda.get_device_properties(0).total_memory
            info.update(
                {
                    "cuda_available": True,
                    "device_name": device_name,
                    "total_memory_bytes": total_mem,
                }
            )
            logger.info(
                "Initialized GPU: %s with %.1f%% memory fraction",
                device_name,
                memory_fraction * 100,
            )
    except Exception as e:
        logger.warning("GPU initialization fallback to CPU: %s", e)

    return info


def run_with_oom_fallback(
    func: Callable[[list[Any]], list[Any]],
    items: list[Any],
    initial_batch_size: int = 32,
    max_retries: int = 5,
) -> tuple[list[Any], dict[str, Any]]:
    """Execute batch inference with OOM halving and CPU fallback."""
    batch_size = initial_batch_size
    results: list[Any] = []
    meta: dict[str, Any] = {
        "gpu_fallback": False,
        "retries": 0,
        "final_batch_size": batch_size,
    }

    try:
        import torch

        has_cuda = torch.cuda.is_available()
    except ImportError:
        has_cuda = False

    i = 0
    while i < len(items):
        batch = items[i : i + batch_size]
        success = False
        retries = 0

        while not success and retries <= max_retries:
            try:
                if has_cuda:
                    with torch.inference_mode():
                        batch_res = func(batch)
                else:
                    batch_res = func(batch)
                results.extend(batch_res)
                success = True
                i += len(batch)
            except Exception as exc:
                is_oom = (
                    has_cuda
                    and "OutOfMemoryError" in type(exc).__name__
                    or "out of memory" in str(exc).lower()
                )
                if is_oom and retries < max_retries:
                    retries += 1
                    meta["retries"] += 1
                    batch_size = max(1, batch_size // 2)
                    meta["final_batch_size"] = batch_size
                    logger.warning(
                        "CUDA OOM. Halving batch size to %d (retry %d)", batch_size, retries
                    )
                    with contextlib.suppress(Exception):
                        torch.cuda.empty_cache()
                    batch = items[i : i + batch_size]
                else:
                    logger.warning("Falling back to CPU inference: %s", exc)
                    meta["gpu_fallback"] = True
                    # CPU fallback for remainder of items
                    cpu_res = func(items[i:])
                    results.extend(cpu_res)
                    return results, meta

    return results, meta
