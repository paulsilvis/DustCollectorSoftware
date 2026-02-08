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
    player: "mpg123"  # or "pygame" or "aplay"
    # Remove: engine, voice, volume, speed_wpm (no longer needed)
"""

from __future__ import annotations

import asyncio
import glob
import logging
import os
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("aqm_announcer")


class _Announcer:
    """
    Modified announcer that plays random pre-generated audio files.
    """
    
    def __init__(self, audio_dir: str, player: str = "mpg123") -> None:
        """
        Initialize the announcer.
        
        Args:
            audio_dir: Path to directory containing unsafe/ and safe/ subdirectories
            player: Audio player to use ("mpg123", "aplay", or "pygame")
        """
        self.audio_dir = Path(audio_dir)
        self.player = player
        self._state: str | None = None
        
        # Load available audio files
        self.unsafe_files = self._load_audio_files("unsafe")
        self.safe_files = self._load_audio_files("safe")
        
        # Validate setup
        self._validate_setup()
        
    def _load_audio_files(self, category: str) -> list[Path]:
        """Load all audio files for a category."""
        category_dir = self.audio_dir / category
        if not category_dir.exists():
            log.warning(f"Audio directory not found: {category_dir}")
            return []
            
        files = list(category_dir.glob("*.mp3"))
        log.info(f"Loaded {len(files)} {category} audio files from {category_dir}")
        return files
        
    def _validate_setup(self) -> None:
        """Validate that audio files and player are available."""
        if not self.unsafe_files:
            log.error(f"No unsafe audio files found in {self.audio_dir}/unsafe/")
            
        if not self.safe_files:
            log.error(f"No safe audio files found in {self.audio_dir}/safe/")
            
        if self.player == "mpg123" and shutil.which("mpg123") is None:
            log.error("mpg123 not found. Install with: sudo apt-get install mpg123")
        elif self.player == "aplay" and shutil.which("aplay") is None:
            log.error("aplay not found. Install with: sudo apt-get install alsa-utils")
        elif self.player == "pygame":
            try:
                import pygame.mixer
            except ImportError:
                log.error("pygame not found. Install with: pip install pygame")
                
    async def _play_audio_mpg123(self, filepath: Path) -> None:
        """Play audio using mpg123 command-line player."""
        cmd = ["mpg123", "-q", str(filepath)]  # -q for quiet (no output)
        
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
                log.error(f"mpg123 failed rc={proc.returncode} err={err}")
        except Exception:
            log.exception("mpg123 playback failed")
            
    async def _play_audio_aplay(self, filepath: Path) -> None:
        """Play audio using aplay command-line player."""
        cmd = ["aplay", "-q", str(filepath)]  # -q for quiet
        
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
                log.error(f"aplay failed rc={proc.returncode} err={err}")
        except Exception:
            log.exception("aplay playback failed")
            
    async def _play_audio_pygame(self, filepath: Path) -> None:
        """Play audio using pygame.mixer."""
        try:
            import pygame.mixer
            
            # Initialize if needed
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                
            # Load and play
            sound = pygame.mixer.Sound(str(filepath))
            channel = sound.play()
            
            # Wait for playback to finish
            while channel.get_busy():
                await asyncio.sleep(0.1)
                
        except Exception:
            log.exception("pygame playback failed")
            
    async def _speak(self, is_unsafe: bool) -> None:
        """
        Play a random audio file for the given state.
        
        Args:
            is_unsafe: True for unsafe air, False for safe air
        """
        # Select random file
        file_list = self.unsafe_files if is_unsafe else self.safe_files
        
        if not file_list:
            log.error(f"No audio files available for {'unsafe' if is_unsafe else 'safe'}")
            return
            
        selected_file = random.choice(file_list)
        
        log.info(f"Playing: {selected_file.name}")
        
        # Play using selected player
        if self.player == "mpg123":
            await self._play_audio_mpg123(selected_file)
        elif self.player == "aplay":
            await self._play_audio_aplay(selected_file)
        elif self.player == "pygame":
            await self._play_audio_pygame(selected_file)
        else:
            log.error(f"Unknown player: {self.player}")
            
    async def on_event(self, ev_type: str) -> None:
        """
        Handle AQM events and play announcements.
        
        This is the same interface as the original announcer.
        """
        if ev_type not in ("aqm.bad", "aqm.good"):
            return

        new_state = "bad" if ev_type == "aqm.bad" else "good"
        
        if self._state is None:
            self._state = new_state
            log.info(f"AQM announce baseline: {self._state}")
            return

        if new_state == self._state:
            return
            
        # State changed - play announcement
        self._state = new_state
        is_unsafe = (new_state == "bad")
        
        await self._speak(is_unsafe)


# =============================================================================
# INTEGRATION HELPER FUNCTIONS
# =============================================================================

def _cfg_get(cfg: Any, keys: list[str], default: Any) -> Any:
    """Get nested config value."""
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
    """Check if config path exists."""
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
    
    This is a drop-in replacement for the original run_aqm_announcer function.
    
    CONFIG EXAMPLE:
        announce:
          enabled: true
          audio_dir: "AudioCoolness"  # or full path: "/home/pi/DustCollectorSoftware/AudioCoolness"
          player: "mpg123"  # or "aplay" or "pygame"
          min_seconds_between: 60.0
    """
    # Prefer top-level "announce:" if present, else fall back to "aqm: announce:"
    use_top = _cfg_has_path(cfg, ["announce"])
    base = ["announce"] if use_top else ["aqm", "announce"]

    # Check if enabled
    enabled = bool(_cfg_get(cfg, base + ["enabled"], True))
    if not enabled:
        log.info("AQM announcer disabled")
        return
        
    # Load config
    audio_dir = str(_cfg_get(cfg, base + ["audio_dir"], "AudioCoolness"))
    player = str(_cfg_get(cfg, base + ["player"], "mpg123"))
    min_seconds_between = float(_cfg_get(cfg, base + ["min_seconds_between"], 60.0))
    
    # Resolve audio_dir to absolute path if needed
    audio_path = Path(audio_dir)
    if not audio_path.is_absolute():
        # Assume relative to current working directory or script location
        audio_path = Path.cwd() / audio_dir
        
    log.info(
        f"AQM announcer (ElevenLabs) running: audio_dir={audio_path} "
        f"player={player} min_seconds_between={min_seconds_between}"
    )
    
    # Create announcer
    announcer = _Announcer(audio_dir=str(audio_path), player=player)
    
    # Subscribe to events
    q = bus.subscribe(maxsize=200)
    
    # Track timing for rate limiting
    import time
    last_announce_ts = 0.0

    while True:
        ev = await q.get()
        ev_type = getattr(ev, "type", "")
        
        # Check rate limiting
        now = time.monotonic()
        if now - last_announce_ts < min_seconds_between:
            if ev_type in ("aqm.bad", "aqm.good"):
                log.info(f"AQM announce suppressed (rate limit): {ev_type}")
            continue
            
        # Process event
        await announcer.on_event(ev_type)
        
        # Update timestamp if announcement was made
        if ev_type in ("aqm.bad", "aqm.good"):
            new_state = "bad" if ev_type == "aqm.bad" else "good"
            if announcer._state == new_state:
                last_announce_ts = now


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    """Test the announcer standalone."""
    import sys
    
    async def test_announcer():
        """Simple test function."""
        print("ElevenLabs Announcer Test")
        print("-" * 50)
        
        # Get audio directory from command line or use default
        audio_dir = sys.argv[1] if len(sys.argv) > 1 else "AudioCoolness"
        
        print(f"Audio directory: {audio_dir}")
        print()
        
        # Create announcer
        announcer = _Announcer(audio_dir=audio_dir, player="mpg123")
        
        print(f"Found {len(announcer.unsafe_files)} unsafe audio files")
        print(f"Found {len(announcer.safe_files)} safe audio files")
        print()
        
        # Test unsafe announcement
        print("Playing random UNSAFE announcement...")
        await announcer._speak(is_unsafe=True)
        await asyncio.sleep(1)
        
        # Test safe announcement
        print("Playing random SAFE announcement...")
        await announcer._speak(is_unsafe=False)
        
        print("\nTest complete!")
    
    asyncio.run(test_announcer())
