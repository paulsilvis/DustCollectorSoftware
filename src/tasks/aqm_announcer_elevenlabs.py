"""
Modified AQM Announcer for ElevenLabs Pre-generated Audio

This is a drop-in replacement for the _speak() method in your existing
aqm_announcer.py. Instead of using espeak-ng, it randomly selects from
pre-generated audio files.

INTEGRATION:
1. Copy this file to your DustCollectorSoftware/ directory
2. In your existing aqm_announcer.py, replace the _Announcer class with this one
3. Update config to point to AudioCoolness directory

CONFIG CHANGES:
In your config file, change:
  announce:
    enabled: true
    audio_dir: "AudioCoolness"  # Path to generated audio files
    player: "mpg123"            # or "pygame" or "aplay"
    min_seconds_between: 60
    post_good_delay_s: 4.0      # wait after fan stops before playing "air is safe"
    # Remove: engine, voice, volume, speed_wpm (no longer needed)
"""

from __future__ import annotations

import asyncio
import logging
import random
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("aqm_announcer")


class _Announcer:
    """
    Announcer that plays random pre-generated audio files.

    Sequence for BAD:  announcement plays → (aqm_policy waits) → fan ON
    Sequence for GOOD: fan OFF → post_good_delay_s → announcement plays
    """

    def __init__(
        self,
        audio_dir: str,
        player: str = "mpg123",
        post_good_delay_s: float = 0.0,
    ) -> None:
        self.audio_dir = Path(audio_dir)
        self.player = player
        self.post_good_delay_s = post_good_delay_s
        self._state: str | None = None

        # Load available audio files
        self.unsafe_files = self._load_audio_files("unsafe")
        self.safe_files = self._load_audio_files("safe")

        self._validate_setup()

    def _load_audio_files(self, category: str) -> list[Path]:
        category_dir = self.audio_dir / category
        if not category_dir.exists():
            log.warning("Audio directory not found: %s", category_dir)
            return []
        files = list(category_dir.glob("*.mp3"))
        log.info("Loaded %d %s audio files from %s", len(files), category, category_dir)
        return files

    def _validate_setup(self) -> None:
        if not self.unsafe_files:
            log.error("No unsafe audio files found in %s/unsafe/", self.audio_dir)
        if not self.safe_files:
            log.error("No safe audio files found in %s/safe/", self.audio_dir)
        if self.player == "mpg123" and shutil.which("mpg123") is None:
            log.error("mpg123 not found. Install with: sudo apt-get install mpg123")
        elif self.player == "aplay" and shutil.which("aplay") is None:
            log.error("aplay not found. Install with: sudo apt-get install alsa-utils")
        elif self.player == "pygame":
            try:
                import pygame.mixer  # noqa: F401
            except ImportError:
                log.error("pygame not found. Install with: pip install pygame")

    async def _play_audio_mpg123(self, filepath: Path) -> None:
        # Use the stable PipeWire/PulseAudio device name rather than hw:N,0
        # so card-number shifts on reboot don't break playback.
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

    async def _play_audio_aplay(self, filepath: Path) -> None:
        cmd = ["aplay", "-q", str(filepath)]
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
                log.error("aplay failed rc=%d err=%s", proc.returncode, err)
        except Exception:
            log.exception("aplay playback failed")

    async def _play_audio_pygame(self, filepath: Path) -> None:
        try:
            import pygame.mixer
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound = pygame.mixer.Sound(str(filepath))
            channel = sound.play()
            while channel.get_busy():
                await asyncio.sleep(0.1)
        except Exception:
            log.exception("pygame playback failed")

    async def _speak(self, is_unsafe: bool) -> None:
        file_list = self.unsafe_files if is_unsafe else self.safe_files
        if not file_list:
            log.error(
                "No audio files available for %s",
                "unsafe" if is_unsafe else "safe",
            )
            return
        selected_file = random.choice(file_list)
        log.info("Playing: %s", selected_file.name)
        if self.player == "mpg123":
            await self._play_audio_mpg123(selected_file)
        elif self.player == "aplay":
            await self._play_audio_aplay(selected_file)
        elif self.player == "pygame":
            await self._play_audio_pygame(selected_file)
        else:
            log.error("Unknown player: %s", self.player)

    async def on_event(self, ev_type: str) -> None:
        """
        Handle AQM events and play announcements.

        BAD:  play immediately (aqm_policy delays fan ON so announcement plays in quiet)
        GOOD: wait post_good_delay_s first (fan is already OFF; let it spin down and
              go quiet before the "air is safe" message plays)
        """
        if ev_type not in ("aqm.bad", "aqm.good"):
            return

        new_state = "bad" if ev_type == "aqm.bad" else "good"

        if self._state is None:
            self._state = new_state
            log.info("AQM announce baseline: %s", self._state)
            return

        if new_state == self._state:
            return

        self._state = new_state
        is_unsafe = (new_state == "bad")

        if not is_unsafe and self.post_good_delay_s > 0:
            log.info(
                "AQM announcer: fan is OFF — waiting %.1fs for it to go quiet "
                "before playing safe-air message",
                self.post_good_delay_s,
            )
            await asyncio.sleep(self.post_good_delay_s)

        await self._speak(is_unsafe)


# =============================================================================
# INTEGRATION HELPER FUNCTIONS
# =============================================================================

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


async def run_aqm_announcer(bus: Any, cfg: Any) -> None:
    """
    Run the AQM announcer with ElevenLabs audio.

    CONFIG EXAMPLE:
        aqm:
          enabled: true
          audio_dir: "AudioCoolness"
          player: "mpg123"
          min_seconds_between: 60
          post_good_delay_s: 4.0   # wait after fan stops before "air is safe" plays
    """
    use_top = _cfg_has_path(cfg, ["aqm"])
    base = ["aqm"] if use_top else ["announce"]

    enabled = bool(_cfg_get(cfg, base + ["enabled"], True))
    if not enabled:
        log.info("AQM announcer disabled")
        return

    audio_dir = str(_cfg_get(cfg, base + ["audio_dir"], "AudioCoolness"))
    player = str(_cfg_get(cfg, base + ["player"], "mpg123"))
    min_seconds_between = float(_cfg_get(cfg, base + ["min_seconds_between"], 60.0))
    post_good_delay_s = float(_cfg_get(cfg, base + ["post_good_delay_s"], 0.0))

    audio_path = Path(audio_dir)
    if not audio_path.is_absolute():
        audio_path = Path.cwd() / audio_dir

    log.info(
        "AQM announcer (ElevenLabs) running: audio_dir=%s player=%s "
        "min_seconds_between=%.0f post_good_delay_s=%.1f",
        audio_path,
        player,
        min_seconds_between,
        post_good_delay_s,
    )

    announcer = _Announcer(
        audio_dir=str(audio_path),
        player=player,
        post_good_delay_s=post_good_delay_s,
    )

    q = bus.subscribe(maxsize=200)
    last_announce_ts = 0.0

    while True:
        ev = await q.get()
        ev_type = getattr(ev, "type", "")

        if ev_type in ("aqm.bad", "aqm.good"):
            now = time.monotonic()
            if now - last_announce_ts < min_seconds_between:
                log.info("AQM announce suppressed (rate limit): %s", ev_type)
                continue

        await announcer.on_event(ev_type)

        if ev_type in ("aqm.bad", "aqm.good"):
            last_announce_ts = time.monotonic()


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    import sys

    async def test_announcer():
        print("ElevenLabs Announcer Test")
        print("-" * 50)
        audio_dir = sys.argv[1] if len(sys.argv) > 1 else "AudioCoolness"
        print(f"Audio directory: {audio_dir}")
        announcer = _Announcer(
            audio_dir=audio_dir,
            player="mpg123",
            post_good_delay_s=4.0,
        )
        print(f"Found {len(announcer.unsafe_files)} unsafe audio files")
        print(f"Found {len(announcer.safe_files)} safe audio files")
        print()
        print("Playing random UNSAFE announcement...")
        await announcer._speak(is_unsafe=True)
        await asyncio.sleep(1)
        print("Playing random SAFE announcement...")
        await announcer._speak(is_unsafe=False)
        print("\nTest complete!")

    asyncio.run(test_announcer())
