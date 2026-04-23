#!/usr/bin/env python3
"""
ElevenLabs Audio Announcement Generator

This script reads announcement_config.yaml and generates all possible
combinations of messages × voices for both unsafe and safe air announcements.

Usage:
    1. Set your ElevenLabs API key:
       export ELEVENLABS_API_KEY="your_key_here"
       
    2. Run the generator:
       python generate_announcements.py
       
    3. Wait for all 400 files to generate (this may take 10-15 minutes)
    
    4. Files will be saved in: DustCollectorSoftware/AudioCoolness/
       - AudioCoolness/unsafe/
       - AudioCoolness/safe/
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from elevenlabs import ElevenLabs, VoiceSettings, save
except ImportError:
    print("ERROR: elevenlabs not installed. Install with: pip install elevenlabs")
    sys.exit(1)


class AudioGenerator:
    def __init__(self, config_path: str = "announcement_config.yaml"):
        """Initialize the generator with configuration."""
        self.config = self._load_config(config_path)
        self.output_base = Path(self.config["settings"]["output_dir"])
        self.model = self.config["settings"]["model"]
        self.client = None  # Will be set in _setup_api_key
        self.stats = {
            "generated": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0
        }
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate the YAML configuration."""
        if not os.path.exists(config_path):
            print(f"ERROR: Config file not found: {config_path}")
            sys.exit(1)
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required sections
        required = ["unsafe_messages", "safe_messages", "unsafe_voices", "safe_voices", "settings"]
        for section in required:
            if section not in config:
                print(f"ERROR: Missing required section in config: {section}")
                sys.exit(1)
                
        return config
        
    def _setup_api_key(self) -> bool:
        """Setup ElevenLabs API key from environment."""
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print("ERROR: ELEVENLABS_API_KEY environment variable not set!")
            print("\nSet it with:")
            print("  export ELEVENLABS_API_KEY='your_key_here'")
            print("\nOr get a free API key at: https://elevenlabs.io/")
            return False
            
        # Create the ElevenLabs client
        self.client = ElevenLabs(api_key=api_key)
        print(f"✓ API key loaded (ends with: ...{api_key[-8:]})")
        return True
        
    def _create_directories(self):
        """Create output directory structure."""
        unsafe_dir = self.output_base / "unsafe"
        safe_dir = self.output_base / "safe"
        
        unsafe_dir.mkdir(parents=True, exist_ok=True)
        safe_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Output directories created:")
        print(f"  - {unsafe_dir}")
        print(f"  - {safe_dir}")
        
    def _generate_audio(
        self, 
        text: str, 
        voice_config: Dict[str, Any],
        output_path: Path,
        skip_existing: bool = True
    ) -> bool:
        """
        Generate a single audio file.
        
        Returns True if successful, False otherwise.
        """
        if skip_existing and output_path.exists():
            self.stats["skipped"] += 1
            return True
            
        try:
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=voice_config.get("stability", 0.5),
                similarity_boost=voice_config.get("similarity_boost", 0.75),
                style=voice_config.get("style", 0.0),
                use_speaker_boost=True
            )
            
            # Generate audio using new API
            audio = self.client.text_to_speech.convert(
                voice_id=voice_config["voice_id"],
                text=text,
                model_id=self.model,
                voice_settings=voice_settings
            )
            
            # Save to file - audio is now a generator, so we need to collect it
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            
            self.stats["generated"] += 1
            return True
            
        except Exception as e:
            print(f"\n✗ FAILED: {output_path.name}")
            print(f"  Error: {str(e)}")
            self.stats["failed"] += 1
            return False
            
    def generate_all(self, skip_existing: bool = True):
        """Generate all audio file combinations."""
        
        print("\n" + "="*70)
        print("ELEVENLABS AUDIO GENERATION")
        print("="*70)
        
        # Calculate totals
        unsafe_count = len(self.config["unsafe_messages"]) * len(self.config["unsafe_voices"])
        safe_count = len(self.config["safe_messages"]) * len(self.config["safe_voices"])
        total = unsafe_count + safe_count
        self.stats["total"] = total
        
        print(f"\nGenerating {total} audio files:")
        print(f"  - Unsafe: {unsafe_count} files ({len(self.config['unsafe_messages'])} messages × {len(self.config['unsafe_voices'])} voices)")
        print(f"  - Safe:   {safe_count} files ({len(self.config['safe_messages'])} messages × {len(self.config['safe_voices'])} voices)")
        print(f"\nOutput: {self.output_base}/")
        
        if skip_existing:
            print("\n⚠ Skipping existing files (use --regenerate to overwrite)")
        
        input("\nPress ENTER to start generation (Ctrl+C to cancel)...")
        
        # Generate unsafe announcements
        print("\n" + "-"*70)
        print("GENERATING UNSAFE ANNOUNCEMENTS")
        print("-"*70)
        self._generate_category("unsafe", self.config["unsafe_messages"], 
                               self.config["unsafe_voices"], skip_existing)
        
        # Generate safe announcements
        print("\n" + "-"*70)
        print("GENERATING SAFE ANNOUNCEMENTS")
        print("-"*70)
        self._generate_category("safe", self.config["safe_messages"],
                               self.config["safe_voices"], skip_existing)
        
        # Summary
        self._print_summary()
        
    def _generate_category(
        self, 
        category: str, 
        messages: List[str], 
        voices: List[Dict[str, Any]],
        skip_existing: bool
    ):
        """Generate all files for a specific category."""
        output_dir = self.output_base / category
        total_for_category = len(messages) * len(voices)
        current = 0
        
        for msg_idx, message in enumerate(messages, 1):
            for voice_config in voices:
                current += 1
                voice_name = voice_config["name"].lower()
                filename = f"{category}_{voice_name}_{msg_idx:03d}.mp3"
                output_path = output_dir / filename
                
                # Progress indicator
                progress = (current / total_for_category) * 100
                status = "○" if skip_existing and output_path.exists() else "●"
                print(f"{status} [{progress:5.1f}%] {filename:<40} ", end="", flush=True)
                
                success = self._generate_audio(message, voice_config, output_path, skip_existing)
                
                if success:
                    if skip_existing and output_path.exists():
                        print("SKIPPED")
                    else:
                        print("✓ DONE")
                else:
                    print("✗ FAILED")
                    
                # Small delay to avoid rate limiting
                if not (skip_existing and output_path.exists()):
                    time.sleep(0.5)
                    
    def _print_summary(self):
        """Print generation summary."""
        print("\n" + "="*70)
        print("GENERATION COMPLETE")
        print("="*70)
        print(f"\nTotal files:     {self.stats['total']}")
        print(f"  ✓ Generated:   {self.stats['generated']}")
        print(f"  ○ Skipped:     {self.stats['skipped']}")
        print(f"  ✗ Failed:      {self.stats['failed']}")
        
        if self.stats['failed'] > 0:
            print(f"\n⚠ WARNING: {self.stats['failed']} files failed to generate")
            print("  Check error messages above for details")
        else:
            print("\n🎉 SUCCESS! All audio files generated successfully!")
            
        print(f"\nFiles saved to: {self.output_base.absolute()}/")
        print("\nNext steps:")
        print("  1. Run preview_announcements.py to listen to samples")
        print("  2. Delete any voices/messages you don't like")
        print("  3. Update your aqm_announcer.py to use these files")
        
    def create_manifest(self):
        """Create a JSON manifest of all generated files."""
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": self.stats["total"],
            "categories": {}
        }
        
        for category in ["unsafe", "safe"]:
            cat_dir = self.output_base / category
            if cat_dir.exists():
                files = sorted([f.name for f in cat_dir.glob("*.mp3")])
                manifest["categories"][category] = {
                    "count": len(files),
                    "files": files
                }
                
        manifest_path = self.output_base / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"\n✓ Manifest saved: {manifest_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate ElevenLabs audio announcements from config"
    )
    parser.add_argument(
        "--config",
        default="announcement_config.yaml",
        help="Path to configuration file (default: announcement_config.yaml)"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate all files, even if they already exist"
    )
    
    args = parser.parse_args()
    
    # Create generator
    generator = AudioGenerator(config_path=args.config)
    
    # Setup API key
    if not generator._setup_api_key():
        sys.exit(1)
        
    # Create directories
    generator._create_directories()
    
    # Generate all audio
    try:
        generator.generate_all(skip_existing=not args.regenerate)
        generator.create_manifest()
    except KeyboardInterrupt:
        print("\n\n⚠ Generation cancelled by user")
        generator._print_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ElevenLabs Audio Announcement Generator

This script reads announcement_config.yaml and generates all possible
combinations of messages × voices for both unsafe and safe air announcements.

Usage:
    1. Set your ElevenLabs API key:
       export ELEVENLABS_API_KEY="your_key_here"
       
    2. Run the generator:
       python generate_announcements.py
       
    3. Wait for all 400 files to generate (this may take 10-15 minutes)
    
    4. Files will be saved in: DustCollectorSoftware/AudioCoolness/
       - AudioCoolness/unsafe/
       - AudioCoolness/safe/
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from elevenlabs import ElevenLabs, VoiceSettings, save
except ImportError:
    print("ERROR: elevenlabs not installed. Install with: pip install elevenlabs")
    sys.exit(1)


class AudioGenerator:
    def __init__(self, config_path: str = "announcement_config.yaml"):
        """Initialize the generator with configuration."""
        self.config = self._load_config(config_path)
        self.output_base = Path(self.config["settings"]["output_dir"])
        self.model = self.config["settings"]["model"]
        self.client = None  # Will be set in _setup_api_key
        self.stats = {
            "generated": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0
        }
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate the YAML configuration."""
        if not os.path.exists(config_path):
            print(f"ERROR: Config file not found: {config_path}")
            sys.exit(1)
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required sections
        required = ["unsafe_messages", "safe_messages", "unsafe_voices", "safe_voices", "settings"]
        for section in required:
            if section not in config:
                print(f"ERROR: Missing required section in config: {section}")
                sys.exit(1)
                
        return config
        
    def _setup_api_key(self) -> bool:
        """Setup ElevenLabs API key from environment."""
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print("ERROR: ELEVENLABS_API_KEY environment variable not set!")
            print("\nSet it with:")
            print("  export ELEVENLABS_API_KEY='your_key_here'")
            print("\nOr get a free API key at: https://elevenlabs.io/")
            return False
            
        # Create the ElevenLabs client
        self.client = ElevenLabs(api_key=api_key)
        print(f"✓ API key loaded (ends with: ...{api_key[-8:]})")
        return True
        
    def _create_directories(self):
        """Create output directory structure."""
        unsafe_dir = self.output_base / "unsafe"
        safe_dir = self.output_base / "safe"
        
        unsafe_dir.mkdir(parents=True, exist_ok=True)
        safe_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Output directories created:")
        print(f"  - {unsafe_dir}")
        print(f"  - {safe_dir}")
        
    def _generate_audio(
        self, 
        text: str, 
        voice_config: Dict[str, Any],
        output_path: Path,
        skip_existing: bool = True
    ) -> bool:
        """
        Generate a single audio file.
        
        Returns True if successful, False otherwise.
        """
        if skip_existing and output_path.exists():
            self.stats["skipped"] += 1
            return True
            
        try:
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=voice_config.get("stability", 0.5),
                similarity_boost=voice_config.get("similarity_boost", 0.75),
                style=voice_config.get("style", 0.0),
                use_speaker_boost=True
            )
            
            # Generate audio using new API
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_config["voice_id"],
                text=text,
                model_id=self.model,
                voice_settings=voice_settings
            )
            
            # Save using the elevenlabs save helper
            save(audio_generator, str(output_path))
            
            self.stats["generated"] += 1
            return True
            
        except Exception as e:
            print(f"\n✗ FAILED: {output_path.name}")
            print(f"  Error: {str(e)}")
            self.stats["failed"] += 1
            return False
            
    def generate_all(self, skip_existing: bool = True):
        """Generate all audio file combinations."""
        
        print("\n" + "="*70)
        print("ELEVENLABS AUDIO GENERATION")
        print("="*70)
        
        # Calculate totals
        unsafe_count = len(self.config["unsafe_messages"]) * len(self.config["unsafe_voices"])
        safe_count = len(self.config["safe_messages"]) * len(self.config["safe_voices"])
        total = unsafe_count + safe_count
        self.stats["total"] = total
        
        print(f"\nGenerating {total} audio files:")
        print(f"  - Unsafe: {unsafe_count} files ({len(self.config['unsafe_messages'])} messages × {len(self.config['unsafe_voices'])} voices)")
        print(f"  - Safe:   {safe_count} files ({len(self.config['safe_messages'])} messages × {len(self.config['safe_voices'])} voices)")
        print(f"\nOutput: {self.output_base}/")
        
        if skip_existing:
            print("\n⚠ Skipping existing files (use --regenerate to overwrite)")
        
        input("\nPress ENTER to start generation (Ctrl+C to cancel)...")
        
        # Generate unsafe announcements
        print("\n" + "-"*70)
        print("GENERATING UNSAFE ANNOUNCEMENTS")
        print("-"*70)
        self._generate_category("unsafe", self.config["unsafe_messages"], 
                               self.config["unsafe_voices"], skip_existing)
        
        # Generate safe announcements
        print("\n" + "-"*70)
        print("GENERATING SAFE ANNOUNCEMENTS")
        print("-"*70)
        self._generate_category("safe", self.config["safe_messages"],
                               self.config["safe_voices"], skip_existing)
        
        # Summary
        self._print_summary()
        
    def _generate_category(
        self, 
        category: str, 
        messages: List[str], 
        voices: List[Dict[str, Any]],
        skip_existing: bool
    ):
        """Generate all files for a specific category."""
        output_dir = self.output_base / category
        total_for_category = len(messages) * len(voices)
        current = 0
        
        for msg_idx, message in enumerate(messages, 1):
            for voice_config in voices:
                current += 1
                voice_name = voice_config["name"].lower()
                filename = f"{category}_{voice_name}_{msg_idx:03d}.mp3"
                output_path = output_dir / filename
                
                # Progress indicator
                progress = (current / total_for_category) * 100
                status = "○" if skip_existing and output_path.exists() else "●"
                print(f"{status} [{progress:5.1f}%] {filename:<40} ", end="", flush=True)
                
                success = self._generate_audio(message, voice_config, output_path, skip_existing)
                
                if success:
                    if skip_existing and output_path.exists():
                        print("SKIPPED")
                    else:
                        print("✓ DONE")
                else:
                    print("✗ FAILED")
                    
                # Small delay to avoid rate limiting
                if not (skip_existing and output_path.exists()):
                    time.sleep(0.5)
                    
    def _print_summary(self):
        """Print generation summary."""
        print("\n" + "="*70)
        print("GENERATION COMPLETE")
        print("="*70)
        print(f"\nTotal files:     {self.stats['total']}")
        print(f"  ✓ Generated:   {self.stats['generated']}")
        print(f"  ○ Skipped:     {self.stats['skipped']}")
        print(f"  ✗ Failed:      {self.stats['failed']}")
        
        if self.stats['failed'] > 0:
            print(f"\n⚠ WARNING: {self.stats['failed']} files failed to generate")
            print("  Check error messages above for details")
        else:
            print("\n🎉 SUCCESS! All audio files generated successfully!")
            
        print(f"\nFiles saved to: {self.output_base.absolute()}/")
        print("\nNext steps:")
        print("  1. Run preview_announcements.py to listen to samples")
        print("  2. Delete any voices/messages you don't like")
        print("  3. Update your aqm_announcer.py to use these files")
        
    def create_manifest(self):
        """Create a JSON manifest of all generated files."""
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": self.stats["total"],
            "categories": {}
        }
        
        for category in ["unsafe", "safe"]:
            cat_dir = self.output_base / category
            if cat_dir.exists():
                files = sorted([f.name for f in cat_dir.glob("*.mp3")])
                manifest["categories"][category] = {
                    "count": len(files),
                    "files": files
                }
                
        manifest_path = self.output_base / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"\n✓ Manifest saved: {manifest_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate ElevenLabs audio announcements from config"
    )
    parser.add_argument(
        "--config",
        default="announcement_config.yaml",
        help="Path to configuration file (default: announcement_config.yaml)"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate all files, even if they already exist"
    )
    
    args = parser.parse_args()
    
    # Create generator
    generator = AudioGenerator(config_path=args.config)
    
    # Setup API key
    if not generator._setup_api_key():
        sys.exit(1)
        
    # Create directories
    generator._create_directories()
    
    # Generate all audio
    try:
        generator.generate_all(skip_existing=not args.regenerate)
        generator.create_manifest()
    except KeyboardInterrupt:
        print("\n\n⚠ Generation cancelled by user")
        generator._print_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
