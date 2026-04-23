"""
Tool Announcer - plays audio announcements when tools turn on/off.

Subscribes to machine.on / machine.off events from the event bus.
Randomly selects from pre-generated ElevenLabs MP3 files.

Audio directory structure:
    AudioCoolness/
        saw_on/     saw_on_001_rachel.mp3 ...
        saw_off/    saw_off_001_rachel.mp3 ...
        lathe_on/   lathe_on_001_rachel.mp3 ...
        lathe_off/  lathe_off_001_rachel.mp3 ...

CONFIG (in config.yaml):
    tool_announce:
      enabled: true
      audio_dir: "AudioCoolness"
      player: "mpg123"
      announce_probability: 0.8   # 0.0-1.0, chance of announcing each event
"""

from __future__ import annotations

import asyncio
import logging
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("tool_announcer")


class _ToolAnnouncer:
    """Plays random pre-generated audio files for tool on/off events."""

    def __init__(self, audio_dir: str, player: str = "mpg123",
                 announce_probability: float = 0.8) -> None:
        self._audio_dir = Path(audio_dir)
        self._player = player
        self._announce_probability = announce_probability

        # Load audio files: _files["saw_on"] = [Path, Path, ...]
        self._files: dict[str, list[Path]] = {}
        self._load_all()
        self._validate()

    def _load_all(self) -> None:
        """Load MP3 files for all tool/state combinations."""
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
        """Warn about any missing audio or player."""
        for category, files in self._files.items():
            if not files:
                log.warning("No audio files found for: %s", category)

        if self._player == "mpg123" and shutil.which("mpg123") is None:
            log.error("mpg123 not found - install with: sudo apt-get install mpg123")

    async def _play(self, filepath: Path) -> None:
        """Play a single MP3 file via mpg123."""
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
        Play a random announcement for tool/state if probability check passes.

        Args:
            tool:  "saw" or "lathe"
            state: "on" or "off"
        """
        # Probability gate
        if random.random() > self._announce_probability:
            log.debug("Announcement skipped (probability): %s %s", tool, state)
            return

        category = f"{tool}_{state}"
        files = self._files.get(category, [])

        if not files:
            log.warning("No audio files for: %s", category)
            return

        chosen = random.choice(files)
        log.info("Playing: %s", chosen.name)
        await self._play(chosen)


# ─────────────────────────────────────────────────────────────────────────────
# Config helpers (same pattern as aqm_announcer_elevenlabs.py)
# ─────────────────────────────────────────────────────────────────────────────

def _cfg_get(cfg: Any, keys: list[str], default: Any) -> Any:
    """Get a nested config value, returning default if not found."""
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
    Run the tool announcer task.
    Subscribe to machine.on / machine.off and play audio announcements.

    Add to main.py:
        from .tasks.tool_announcer import run_tool_announcer
        tg.create_task(run_tool_announcer(bus, cfg), name="tool_announcer")
    """
    base = ["tool_announce"]

    enabled = bool(_cfg_get(cfg, base + ["enabled"], True))
    if not enabled:
        log.info("Tool announcer disabled")
        return

    audio_dir = str(_cfg_get(cfg, base + ["audio_dir"], "AudioCoolness"))
    player = str(_cfg_get(cfg, base + ["player"], "mpg123"))
    probability = float(_cfg_get(cfg, base + ["announce_probability"], 0.8))

    # Resolve relative path from cwd
    audio_path = Path(audio_dir)
    if not audio_path.is_absolute():
        audio_path = Path.cwd() / audio_dir

    log.info(
        "Tool announcer running: audio_dir=%s player=%s probability=%.2f",
        audio_path, player, probability,
    )

    announcer = _ToolAnnouncer(
        audio_dir=str(audio_path),
        player=player,
        announce_probability=probability,
    )

    # Events: saw.on, saw.off, lathe.on, lathe.off (published by adc_watch)
    supported_events = {"saw.on", "saw.off", "lathe.on", "lathe.off"}

    q = bus.subscribe(maxsize=200)

    while True:
        ev = await q.get()
        ev_type = getattr(ev, "type", "")

        if ev_type not in supported_events:
            continue

        # "saw.on" -> tool="saw", state="on"
        tool, state = ev_type.split(".")
        await announcer.announce(tool, state)


# ─────────────────────────────────────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    async def _test() -> None:
        audio_dir = sys.argv[1] if len(sys.argv) > 1 else "AudioCoolness"
        print(f"Tool Announcer Test - audio_dir={audio_dir}")
        print("-" * 50)

        announcer = _ToolAnnouncer(audio_dir=audio_dir, announce_probability=1.0)

        for tool in ("saw", "lathe"):
            for state in ("on", "off"):
                print(f"\nPlaying {tool} {state}...")
                await announcer.announce(tool, state)
                await asyncio.sleep(0.5)

        print("\nTest complete!")

    asyncio.run(_test())
