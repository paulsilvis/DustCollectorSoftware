"""
Tool Announcer - plays audio announcements when tools turn on/off.

Sequencing:
    ON:  saw.on  -> announcement plays -> saw.on.ready -> gate opens + collector on
    OFF: saw.off -> gate closes + collector off immediately -> close_sound_delay_s -> announcement

CONFIG (in config.yaml):
    tool_announce:
      enabled: true
      audio_dir: "AudioCoolness"
      player: "mpg123"
      announce_probability: 0.8   # 0.0-1.0, chance of announcing each event

    timing:
      close_sound_delay_s: 5.0   # delay after tool.off before the off announcement
"""

from __future__ import annotations

import asyncio
import logging
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..events import Event

log = logging.getLogger("tool_announcer")


class _ToolAnnouncer:
    """Plays random pre-generated audio files for tool on/off events."""

    def __init__(
        self,
        bus: Any,
        audio_dir: str,
        player: str = "mpg123",
        announce_probability: float = 0.8,
        close_sound_delay_s: float = 5.0,
    ) -> None:
        self._bus = bus
        self._audio_dir = Path(audio_dir)
        self._player = player
        self._announce_probability = announce_probability
        self._close_sound_delay_s = close_sound_delay_s

        self._files: dict[str, list[Path]] = {}
        self._load_all()
        self._validate()

    def _load_all(self) -> None:
        for category in ("saw_on", "saw_off", "lathe_on", "lathe_off"):
            cat_dir = self._audio_dir / category
            if cat_dir.exists():
                files = sorted(cat_dir.glob("*.mp3"))
                self._files[category] = files
                log.info("Loaded %d files from %s", len(files), cat_dir)
            else:
                self._files[category] = []
                log.warning("Audio directory not found: %s", cat_dir)

    def _validate(self) -> None:
        for category, files in self._files.items():
            if not files:
                log.warning("No audio files found for: %s", category)
        if self._player == "mpg123" and shutil.which("mpg123") is None:
            log.error("mpg123 not found - install with: sudo apt-get install mpg123")

    async def _play(self, filepath: Path) -> None:
        cmd = ["mpg123", "-q", "-a", "Z407", str(filepath)]
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
                log.error("mpg123 failed rc=%d err=%s", proc.returncode, err)
        except Exception:
            log.exception("mpg123 playback failed")

    async def announce(self, tool: str, state: str) -> None:
        """
        ON:  play audio, then publish {tool}.on.ready so gate + collector act.
        OFF: gate + collector already acted on {tool}.off directly;
             wait close_sound_delay_s for motor/gate to settle, then play.
        """
        category = f"{tool}_{state}"
        files = self._files.get(category, [])
        skip = random.random() > self._announce_probability

        if state == "on":
            if not skip and files:
                chosen = random.choice(files)
                log.info("Playing: %s", chosen.name)
                await self._play(chosen)
            elif skip:
                log.debug("Announcement skipped (probability): %s %s", tool, state)
            else:
                log.warning("No audio files for: %s", category)

            # Always publish .on.ready so gate + collector are never blocked.
            ready_event = Event.now(f"{tool}.on.ready", src="tool_announcer")
            await self._bus.publish(ready_event)
            log.debug("Published %s", ready_event.type)

        else:  # state == "off"
            # Gate + collector acted on {tool}.off directly.
            # Wait for motor/gate to settle, then play in the quiet.
            if self._close_sound_delay_s > 0:
                log.info(
                    "tool-off: waiting %.1fs before playing close sound",
                    self._close_sound_delay_s,
                )
                await asyncio.sleep(self._close_sound_delay_s)

            if not skip and files:
                chosen = random.choice(files)
                log.info("Playing: %s", chosen.name)
                await self._play(chosen)
            elif skip:
                log.debug("Announcement skipped (probability): %s %s", tool, state)
            else:
                log.warning("No audio files for: %s", category)


# ─────────────────────────────────────────────────────────────────────────────
# Config helpers
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Task entry point
# ─────────────────────────────────────────────────────────────────────────────

async def run_tool_announcer(bus: Any, cfg: Any) -> None:
    """
    ON  path: listens to {tool}.on, plays audio, publishes {tool}.on.ready
    OFF path: listens to {tool}.off, waits close_sound_delay_s, plays audio
              (gate + SSR act on {tool}.off directly)
    """
    base = ["tool_announce"]

    enabled = bool(_cfg_get(cfg, base + ["enabled"], True))
    if not enabled:
        log.info("Tool announcer disabled")
        return

    audio_dir = str(_cfg_get(cfg, base + ["audio_dir"], "AudioCoolness"))
    player = str(_cfg_get(cfg, base + ["player"], "mpg123"))
    probability = float(_cfg_get(cfg, base + ["announce_probability"], 0.8))
    close_sound_delay_s = float(
        _cfg_get(cfg, ["timing", "close_sound_delay_s"], 5.0)
    )

    audio_path = Path(audio_dir)
    if not audio_path.is_absolute():
        audio_path = Path.cwd() / audio_dir

    log.info(
        "Tool announcer running: audio_dir=%s player=%s probability=%.2f"
        " close_sound_delay_s=%.1f",
        audio_path, player, probability, close_sound_delay_s,
    )

    announcer = _ToolAnnouncer(
        bus=bus,
        audio_dir=str(audio_path),
        player=player,
        announce_probability=probability,
        close_sound_delay_s=close_sound_delay_s,
    )

    supported_events = {"saw.on", "saw.off", "lathe.on", "lathe.off"}
    q = bus.subscribe(maxsize=200)

    while True:
        ev = await q.get()
        ev_type = getattr(ev, "type", "")
        if ev_type not in supported_events:
            continue
        tool, state = ev_type.split(".")
        await announcer.announce(tool, state)


# ─────────────────────────────────────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    class _FakeBus:
        async def publish(self, ev: Any) -> None:
            print(f"  [bus] published: {ev.type}")

    async def _test() -> None:
        audio_dir = sys.argv[1] if len(sys.argv) > 1 else "AudioCoolness"
        print(f"Tool Announcer Test - audio_dir={audio_dir}")
        print("-" * 50)
        announcer = _ToolAnnouncer(
            bus=_FakeBus(),
            audio_dir=audio_dir,
            announce_probability=1.0,
            close_sound_delay_s=5.0,
        )
        for tool in ("saw", "lathe"):
            for state in ("on", "off"):
                print(f"\nPlaying {tool} {state}...")
                await announcer.announce(tool, state)
                await asyncio.sleep(0.5)
        print("\nTest complete!")

    asyncio.run(_test())
