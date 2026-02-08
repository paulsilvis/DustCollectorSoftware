#!/usr/bin/env python3
"""
ElevenLabs Audio Announcement Preview Tool

This tool helps you listen to, test, and curate your generated audio announcements.

Features:
  - Play random samples from each category
  - Play all files in a category
  - List all generated files
  - Test the announcer integration
  - Delete files you don't like

Usage:
    python preview_announcements.py [--audio-dir AudioCoolness]
"""

import argparse
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import List


class AudioPreview:
    """Tool for previewing and testing audio announcements."""
    
    def __init__(self, audio_dir: str = "AudioCoolness"):
        """Initialize the preview tool."""
        self.audio_dir = Path(audio_dir)
        self.player = self._find_player()
        
        if not self.audio_dir.exists():
            print(f"ERROR: Audio directory not found: {self.audio_dir}")
            print("\nRun generate_announcements.py first to create audio files.")
            sys.exit(1)
            
        # Load files
        self.unsafe_files = self._load_files("unsafe")
        self.safe_files = self._load_files("safe")
        
    def _find_player(self) -> str:
        """Find an available audio player."""
        players = ["mpg123", "aplay", "ffplay"]
        for player in players:
            import shutil
            if shutil.which(player):
                return player
        
        print("ERROR: No audio player found!")
        print("Install one with: sudo apt-get install mpg123")
        sys.exit(1)
        
    def _load_files(self, category: str) -> List[Path]:
        """Load all audio files for a category."""
        cat_dir = self.audio_dir / category
        if not cat_dir.exists():
            return []
        return sorted(cat_dir.glob("*.mp3"))
        
    def _play_file(self, filepath: Path, show_info: bool = True):
        """Play a single audio file."""
        if show_info:
            print(f"\n♪ Playing: {filepath.name}")
            
        cmd = [self.player]
        if self.player == "mpg123":
            cmd.append("-q")  # Quiet mode
        elif self.player == "aplay":
            cmd.append("-q")
        
        cmd.append(str(filepath))
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"✗ Playback failed: {e}")
        except KeyboardInterrupt:
            print("\n⏸ Playback interrupted")
            raise
            
    def show_summary(self):
        """Show summary of available files."""
        print("\n" + "="*70)
        print("AUDIO LIBRARY SUMMARY")
        print("="*70)
        print(f"\nDirectory: {self.audio_dir.absolute()}")
        print(f"\nUnsafe announcements: {len(self.unsafe_files)} files")
        print(f"Safe announcements:   {len(self.safe_files)} files")
        print(f"Total:                {len(self.unsafe_files) + len(self.safe_files)} files")
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in self.unsafe_files + self.safe_files)
        print(f"Total size:           {total_size / 1024 / 1024:.1f} MB")
        
        # Group by voice
        print("\n" + "-"*70)
        print("FILES BY VOICE")
        print("-"*70)
        
        for category, files in [("Unsafe", self.unsafe_files), ("Safe", self.safe_files)]:
            voices = {}
            for f in files:
                # Extract voice from filename: category_voice_###.mp3
                parts = f.stem.split("_")
                if len(parts) >= 2:
                    voice = parts[1]
                    voices[voice] = voices.get(voice, 0) + 1
                    
            print(f"\n{category}:")
            for voice, count in sorted(voices.items()):
                print(f"  {voice:15} : {count:3} files")
                
    def play_random_samples(self, count: int = 5):
        """Play random samples from each category."""
        print("\n" + "="*70)
        print(f"PLAYING {count} RANDOM SAMPLES FROM EACH CATEGORY")
        print("="*70)
        
        print("\n" + "-"*70)
        print("UNSAFE ANNOUNCEMENTS")
        print("-"*70)
        
        unsafe_samples = random.sample(self.unsafe_files, min(count, len(self.unsafe_files)))
        for i, f in enumerate(unsafe_samples, 1):
            print(f"\n[{i}/{len(unsafe_samples)}]", end=" ")
            self._play_file(f)
            time.sleep(0.5)
            
        print("\n" + "-"*70)
        print("SAFE ANNOUNCEMENTS")
        print("-"*70)
        
        safe_samples = random.sample(self.safe_files, min(count, len(self.safe_files)))
        for i, f in enumerate(safe_samples, 1):
            print(f"\n[{i}/{len(safe_samples)}]", end=" ")
            self._play_file(f)
            time.sleep(0.5)
            
        print("\n✓ Sample playback complete!")
        
    def play_all(self, category: str):
        """Play all files in a category."""
        files = self.unsafe_files if category == "unsafe" else self.safe_files
        
        print(f"\n{'='*70}")
        print(f"PLAYING ALL {category.upper()} ANNOUNCEMENTS ({len(files)} files)")
        print("="*70)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            for i, f in enumerate(files, 1):
                print(f"[{i}/{len(files)}]", end=" ")
                self._play_file(f)
                time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n\n⏸ Playback stopped")
            
    def play_by_voice(self, category: str, voice: str):
        """Play all files for a specific voice."""
        files = self.unsafe_files if category == "unsafe" else self.safe_files
        voice_files = [f for f in files if f"_{voice}_" in f.name]
        
        if not voice_files:
            print(f"No files found for voice '{voice}' in {category}")
            return
            
        print(f"\n{'='*70}")
        print(f"PLAYING {voice.upper()} VOICE ({len(voice_files)} files)")
        print("="*70)
        
        try:
            for i, f in enumerate(voice_files, 1):
                print(f"[{i}/{len(voice_files)}]", end=" ")
                self._play_file(f)
                time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n\n⏸ Playback stopped")
            
    def list_files(self, category: str = None):
        """List all files."""
        if category:
            files = self.unsafe_files if category == "unsafe" else self.safe_files
            print(f"\n{category.upper()} FILES:")
            for f in files:
                size_kb = f.stat().st_size / 1024
                print(f"  {f.name:50} ({size_kb:6.1f} KB)")
        else:
            self.list_files("unsafe")
            self.list_files("safe")
            
    def interactive_menu(self):
        """Show interactive menu."""
        while True:
            print("\n" + "="*70)
            print("AUDIO PREVIEW MENU")
            print("="*70)
            print("\n1. Show summary")
            print("2. Play random samples (5 from each category)")
            print("3. Play ALL unsafe announcements")
            print("4. Play ALL safe announcements")
            print("5. Play specific voice")
            print("6. List all files")
            print("7. Test announcer integration")
            print("8. Delete files")
            print("0. Exit")
            
            choice = input("\nSelect option (0-8): ").strip()
            
            try:
                if choice == "0":
                    print("\nGoodbye!")
                    break
                elif choice == "1":
                    self.show_summary()
                elif choice == "2":
                    self.play_random_samples(5)
                elif choice == "3":
                    self.play_all("unsafe")
                elif choice == "4":
                    self.play_all("safe")
                elif choice == "5":
                    self._interactive_voice_playback()
                elif choice == "6":
                    self.list_files()
                elif choice == "7":
                    self._test_announcer()
                elif choice == "8":
                    self._interactive_delete()
                else:
                    print("Invalid option")
            except KeyboardInterrupt:
                print("\n\nReturning to menu...")
                continue
                
    def _interactive_voice_playback(self):
        """Interactive voice selection and playback."""
        print("\nSelect category:")
        print("1. Unsafe")
        print("2. Safe")
        
        cat_choice = input("Choice (1-2): ").strip()
        category = "unsafe" if cat_choice == "1" else "safe"
        
        # Get available voices
        files = self.unsafe_files if category == "unsafe" else self.safe_files
        voices = set()
        for f in files:
            parts = f.stem.split("_")
            if len(parts) >= 2:
                voices.add(parts[1])
                
        voices = sorted(voices)
        
        print(f"\nAvailable voices in {category}:")
        for i, voice in enumerate(voices, 1):
            print(f"{i}. {voice}")
            
        voice_idx = input(f"\nSelect voice (1-{len(voices)}): ").strip()
        try:
            selected_voice = voices[int(voice_idx) - 1]
            self.play_by_voice(category, selected_voice)
        except (ValueError, IndexError):
            print("Invalid selection")
            
    def _test_announcer(self):
        """Test the announcer integration."""
        print("\n" + "="*70)
        print("TESTING ANNOUNCER INTEGRATION")
        print("="*70)
        
        try:
            import asyncio
            import sys
            
            # Add parent directory to path to import announcer
            sys.path.insert(0, str(Path(__file__).parent))
            
            from aqm_announcer_elevenlabs import _Announcer
            
            async def test():
                announcer = _Announcer(audio_dir=str(self.audio_dir), player=self.player)
                
                print("\nTest 1: Playing UNSAFE announcement...")
                await announcer._speak(is_unsafe=True)
                await asyncio.sleep(1)
                
                print("\nTest 2: Playing SAFE announcement...")
                await announcer._speak(is_unsafe=False)
                
                print("\n✓ Announcer test complete!")
                
            asyncio.run(test())
            
        except ImportError as e:
            print(f"\n✗ Could not import announcer module: {e}")
            print("Make sure aqm_announcer_elevenlabs.py is in the same directory")
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            
    def _interactive_delete(self):
        """Interactive file deletion."""
        print("\n⚠ WARNING: This will permanently delete files!")
        print("\nWhat would you like to delete?")
        print("1. Delete specific voice (all messages for that voice)")
        print("2. Delete specific file")
        print("3. Cancel")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            self._delete_voice()
        elif choice == "2":
            self._delete_file()
        else:
            print("Cancelled")
            
    def _delete_voice(self):
        """Delete all files for a specific voice."""
        # Implementation left as exercise - lists voices, confirms, deletes
        print("\nFeature coming soon! For now, delete manually from:")
        print(f"  {self.audio_dir}/unsafe/")
        print(f"  {self.audio_dir}/safe/")
        
    def _delete_file(self):
        """Delete a specific file."""
        # Implementation left as exercise
        print("\nFeature coming soon! For now, delete manually from:")
        print(f"  {self.audio_dir}/unsafe/")
        print(f"  {self.audio_dir}/safe/")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Preview and test ElevenLabs audio announcements"
    )
    parser.add_argument(
        "--audio-dir",
        default="AudioCoolness",
        help="Path to audio directory (default: AudioCoolness)"
    )
    parser.add_argument(
        "--random",
        type=int,
        metavar="N",
        help="Play N random samples from each category and exit"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all files and exit"
    )
    
    args = parser.parse_args()
    
    # Create preview tool
    preview = AudioPreview(audio_dir=args.audio_dir)
    
    # Handle command-line modes
    if args.random:
        preview.show_summary()
        preview.play_random_samples(args.random)
    elif args.list:
        preview.list_files()
    else:
        # Interactive mode
        preview.show_summary()
        preview.interactive_menu()


if __name__ == "__main__":
    main()
