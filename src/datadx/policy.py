"""Policy loader and configuration management.

Provides type-safe policy parameters with default fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Policy:
    """Configuration policy governing detection and verdicts."""

    borderline_band: float = 0.02
    markup_languages: list[str] = field(
        default_factory=lambda: [
            "html",
            "xml",
            "jsx",
            "tsx",
            "vue",
            "svelte",
            "markdown",
        ]
    )
    phone_regions: list[str] = field(default_factory=lambda: ["IN", "GB", "US"])
    thresholds: dict[str, Any] = field(default_factory=dict)
    raw_config: dict[str, Any] = field(default_factory=dict)

    def get_threshold(self, name: str, default: Any) -> Any:
        return self.thresholds.get(name, default)


def load_policy(path: str | Path | None = None) -> Policy:
    """Load policy from YAML file or fallback to default policy."""
    if path is not None and Path(path).is_file():
        policy_path = Path(path)
    else:
        policy_path = Path(__file__).parent / "policy.default.yaml"

    with open(policy_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return Policy(
        borderline_band=float(data.get("borderline_band", 0.02)),
        markup_languages=list(
            data.get(
                "markup_languages",
                ["html", "xml", "jsx", "tsx", "vue", "svelte", "markdown"],
            )
        ),
        phone_regions=list(data.get("phone_regions", ["IN", "GB", "US"])),
        thresholds=dict(data.get("thresholds", {})),
        raw_config=data,
    )
