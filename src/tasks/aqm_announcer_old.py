from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any

from ..event_bus import EventBus

log = logging.getLogger("aqm_announcer")


def _cfg_get(cfg: Any, keys: list[str], default: Any) -> Any:
    raw = getattr(cfg, "raw", None)
    if not isinstance(raw, dict):
        return default
    cur: Any = raw
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _cfg_has_path(cfg: Any, keys: list[str]) -> bool:
    raw = getattr(cfg, "raw", None)
    if not isinstance(raw, dict):
        return False
    cur: Any = raw
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return False
        cur = cur[k]
    return True


@dataclass(frozen=True)
class AnnouncerConfig:
    enabled: bool
    min_seconds_between_announcements: float
    engine: str
    voice: str
    volume: int
    speed_wpm: int
    unsafe_text: str
    safe_text: str


def _preview_text(s: str, n: int = 40) -> str:
    s2 = " ".join(str(s).split())
    if len(s2) <= n:
        return s2
    return s2[:n] + "..."


def _load_announcer_config(cfg: Any) -> AnnouncerConfig:
    """
    Preferred config location:
      announce: { enabled, min_seconds_between, engine, voice, volume, speed_wpm,
                  unsafe_text, safe_text }

    Backward-compatible fallback:
      aqm: { announce: {...same keys...} }
    """
    # Prefer top-level "announce:" if present, else fall back to "aqm: announce:"
    use_top = _cfg_has_path(cfg, ["announce"])
    base = ["announce"] if use_top else ["aqm", "announce"]

    enabled = bool(_cfg_get(cfg, base + ["enabled"], True))
    min_s = float(_cfg_get(cfg, base + ["min_seconds_between"], 60.0))
    engine = str(_cfg_get(cfg, base + ["engine"], "espeak-ng"))
    voice = str(_cfg_get(cfg, base + ["voice"], "en-us"))
    volume = int(_cfg_get(cfg, base + ["volume"], 200))
    speed = int(_cfg_get(cfg, base + ["speed_wpm"], 155))

    default_unsafe = (
        "Warning!! Warning!! Warning!! Air quality is no longer safe, "
        "and the filter has been activated"
    )
    default_safe = "All clear! Air quality is now considered safe."

    unsafe_text = str(_cfg_get(cfg, base + ["unsafe_text"], default_unsafe))
    safe_text = str(_cfg_get(cfg, base + ["safe_text"], default_safe))

    return AnnouncerConfig(
        enabled=enabled,
        min_seconds_between_announcements=min_s,
        engine=engine,
        voice=voice,
        volume=volume,
        speed_wpm=speed,
        unsafe_text=unsafe_text,
        safe_text=safe_text,
    )


class _Announcer:
    def __init__(self, cfg: AnnouncerConfig) -> None:
        self._cfg = cfg
        self._state: str | None = None
        self._last_announce_ts = 0.0

    async def _speak(self, text: str) -> None:
        cfg = self._cfg

        if shutil.which(cfg.engine) is None:
            log.error("Speech engine not found: %s", cfg.engine)
            return

        # espeak-ng CLI is stable: -v, -a (amplitude), -s (speed).
        # If you switch engines later, we can branch on cfg.engine.
        cmd = [
            cfg.engine,
            "-v",
            cfg.voice,
            "-a",
            str(cfg.volume),
            "-s",
            str(cfg.speed_wpm),
            text,
        ]

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                err = (proc.stderr or "").strip()
                log.error("Speech engine failed rc=%s err=%s", proc.returncode, err)
        except Exception:
            log.exception("Speech announce failed")

    async def on_event(self, ev_type: str) -> None:
        if ev_type not in ("aqm.bad", "aqm.good"):
            return

        new_state = "bad" if ev_type == "aqm.bad" else "good"
        if self._state is None:
            self._state = new_state
            log.info("AQM announce baseline: %s", self._state)
            return

        if new_state == self._state:
            return

        now = time.monotonic()
        if (
            now - self._last_announce_ts
            < self._cfg.min_seconds_between_announcements
        ):
            log.info("AQM announce suppressed (rate limit): %s", new_state)
            self._state = new_state
            return

        self._state = new_state
        self._last_announce_ts = now

        text = self._cfg.unsafe_text if new_state == "bad" else self._cfg.safe_text
        log.warning("AQM announce: %s", text)
        await self._speak(text)


async def run_aqm_announcer(bus: EventBus, cfg: Any) -> None:
    """Announce AQM transitions using a speech engine (default: espeak-ng)."""
    a_cfg = _load_announcer_config(cfg)

    if not a_cfg.enabled:
        log.info("AQM announcer disabled")
        return

    log.info(
        "AQM announcer running: engine=%s voice=%s volume=%d speed_wpm=%d "
        "min_seconds_between=%.1f safe_text(len=%d '%s') unsafe_text(len=%d '%s')",
        a_cfg.engine,
        a_cfg.voice,
        a_cfg.volume,
        a_cfg.speed_wpm,
        a_cfg.min_seconds_between_announcements,
        len(a_cfg.safe_text),
        _preview_text(a_cfg.safe_text),
        len(a_cfg.unsafe_text),
        _preview_text(a_cfg.unsafe_text),
    )

    announcer = _Announcer(a_cfg)
    q = bus.subscribe(maxsize=200)

    while True:
        ev = await q.get()
        await announcer.on_event(getattr(ev, "type", ""))
