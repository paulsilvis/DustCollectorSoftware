from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


def _env_truthy(name: str) -> bool | None:
    v = os.environ.get(name)
    if v is None:
        return None
    v = v.strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return None


@dataclass(frozen=True)
class AppConfig:
    raw: Dict[str, Any]
    mock: bool
    log_level: str

    @staticmethod
    def load(path: str) -> "AppConfig":
        p = Path(path)
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        # Base config value
        mock_cfg = bool(raw.get("system", {}).get("mock", False))
        # Env override (lets you run MOCK=true without editing config)
        mock_env = _env_truthy("MOCK")
        mock = mock_env if mock_env is not None else mock_cfg
        log_level = str(raw.get("logging", {}).get("level", "INFO")).upper()
        return AppConfig(raw=raw, mock=mock, log_level=log_level)
