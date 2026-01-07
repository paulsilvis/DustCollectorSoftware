from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


def _is_mock_from_raw(raw: Dict[str, Any]) -> bool:
    hw = raw.get("hardware", {}) or {}
    mode = str(hw.get("mode", "mock")).strip().lower()
    return mode != "real"


@dataclass(frozen=True)
class AppConfig:
    """
    Immutable application configuration.

    During the cutover we keep cfg.mock as a derived compatibility flag
    because several tasks still branch on it. It is derived solely from
    config (hardware.mode) to avoid multiple conflicting switches.
    """
    raw: Dict[str, Any]
    log_level: str
    mock: bool

    @staticmethod
    def load(path: str) -> "AppConfig":
        p = Path(path)
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

        log_level = (
            raw.get("logging", {})
            .get("level", "INFO")
        )

        return AppConfig(
            raw=raw,
            log_level=str(log_level).upper(),
            mock=_is_mock_from_raw(raw),
        )
