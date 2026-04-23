#!/usr/bin/env python3
"""
Dust Collector Tool Announcement Generator
Generates audio files for tool on/off events using ElevenLabs API.

Directory structure:
    DustCollectorSoftware/
    └── AudioCoolness/
        ├── saw_on/         saw_on_001_rachel.mp3 ...
        ├── saw_off/        saw_off_001_rachel.mp3 ...
        ├── lathe_on/       lathe_on_001_rachel.mp3 ...
        └── lathe_off/      lathe_off_001_rachel.mp3 ...

Usage:
    export ELEVENLABS_API_KEY="your_key_here"
    python3 generate_tool_announcements.py          # Generate all missing files
    python3 generate_tool_announcements.py --dry-run  # Show what would be generated
    python3 generate_tool_announcements.py --tool saw  # Just saw files
    python3 generate_tool_announcements.py --tool lathe # Just lathe files
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

# ─────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────

# Find project root (script lives in AudioCoolness/, project root is one up)
SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == 'AudioCoolness' else SCRIPT_DIR
AUDIO_ROOT   = PROJECT_ROOT / 'AudioCoolness'

# ElevenLabs voices - name: voice_id
VOICES = {
    'rachel':  '21m00Tcm4TlvDq8ikWAM',
    'clyde':   '2EiwWnXFnvU5JabPnv8n',
    'domi':    'AZnzlk1XvdvUeBnXmlld',
    'fin':     'D38z5RcWu1voky8WS1ja',
    'jessica': 'cgSgspJ2msm6clMCkdW9',
    'eric':    'cjVigY5qzO86Huf0OWal',
    'drew':    'jsCqWAovK2LkecY7zXl4',
    'lily':    'pFZP5JQG7iQjIQuC4Bku',
    'adam':    'pNInz6obpgDQGcFmaJgB',
    'bill':    'pqHfZKP75CvOlQylNhV4',
}

# Delay between API calls (seconds) - be polite to the API
API_DELAY = 0.5

# ─────────────────────────────────────────────────────────
# Message pools
# ─────────────────────────────────────────────────────────

MESSAGES = {

    'saw_on': [
        "Table saw activated. Keep those hands clear.",
        "Saw is running. Remember your push stick.",
        "Let's make some cuts. Safety first.",
        "Saw spinning up. Eye protection on?",
        "Cutting time. Measure twice, cut once.",
        "Time to rip some wood. Stay focused.",
        "Blade is live. Respect the tool.",
        "Let's turn wood into smaller wood.",
        "Alright, let's make some sawdust.",
        "Ready to cut. Push stick handy?",
        "Saw running. No loose clothing please.",
        "Time to transform this lumber.",
        "Blade spinning. Hand position good?",
        "Let's do this safely.",
        "Saw active. Featherboard in place?",
        "Ready for precision cutting.",
        "The saw is yours. Make it count.",
        "Cutting mode engaged. Stay sharp.",
        "Saw on. Fence set correctly?",
        "Time to make some beautiful cuts.",
    ],

    'saw_off': [
        "Table saw stopped.",
        "Saw is off. Good session.",
        "Cutting complete. Nice work.",
        "All fingers accounted for? Great job.",
        "Good work keeping it safe.",
        "Another successful cut. Well done.",
        "Blade stopped. Let it come to a full stop before reaching in.",
        "Safe shutdown. That's how it's done.",
        "That's a wrap on the saw.",
        "Clean cuts achieved. Excellent.",
        "Excellent work at the saw.",
        "Saw off. Time to check your work.",
        "Mission accomplished at the saw.",
        "Nice cutting session today.",
        "Saw secured. Great job.",
        "Another one in the books.",
        "Perfect. Saw is off and safe.",
        "Good cutting. Stay sharp next time too.",
        "Saw down safely. Well crafted.",
        "Blade stopped. Admire those cuts.",
    ],

    'lathe_on': [
        "Lathe is spinning. Goggles on?",
        "Lathe activated. Secure your workpiece.",
        "Time to turn. Tool rest set?",
        "Lathe on. Check your speed setting.",
        "Let's make some turnings.",
        "Spinning up the lathe. Stay alert.",
        "Lathe running. Hand position ready?",
        "Ready to shape some wood.",
        "Lathe engaged. Sharp tools?",
        "Time for some turning magic.",
        "Let's make the chips fly.",
        "Lathe is live. Respect the spin.",
        "Turning time. Face shield down?",
        "The lathe is all yours.",
        "Ready to create something round.",
        "Lathe spinning. Tailstock secure?",
        "Let's turn this into art.",
        "Active lathe. Catch cup in place?",
        "Spinning wood mode activated.",
        "Lathe on. Make something beautiful.",
    ],

    'lathe_off': [
        "Lathe stopped.",
        "Lathe is off. Good session.",
        "Turning complete. Nice work.",
        "Beautiful turning. Well done.",
        "Smooth finish achieved.",
        "Lathe secured. Excellent work.",
        "Another beautiful turning complete.",
        "Spindle stopped safely.",
        "That's a wrap on the lathe.",
        "Excellent turning session today.",
        "Lathe off. Admire your work.",
        "Clean shutdown. That's how it's done.",
        "Perfect. Lathe is down.",
        "Great work at the lathe.",
        "Turning finished successfully.",
        "Lathe secured. Nice craftsmanship.",
        "Another one completed beautifully.",
        "Spindle stopped. Check for smoothness.",
        "Beautiful work today at the lathe.",
        "Lathe down. Well crafted as always.",
    ],

}

# ─────────────────────────────────────────────────────────
# API call
# ─────────────────────────────────────────────────────────

def generate_audio_file(text: str, voice_id: str, output_path: Path, api_key: str) -> bool:
    """Generate a single audio file via ElevenLabs REST API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"   ❌ API error {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False

# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate tool announcement audio files')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be generated without making API calls')
    parser.add_argument('--tool', choices=['saw', 'lathe', 'all'], default='all',
                        help='Which tool to generate files for (default: all)')
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key and not args.dry_run:
        print("❌ Error: ELEVENLABS_API_KEY environment variable not set")
        print("   export ELEVENLABS_API_KEY='your_key_here'")
        sys.exit(1)
    
    # Filter messages by tool
    if args.tool == 'saw':
        categories = ['saw_on', 'saw_off']
    elif args.tool == 'lathe':
        categories = ['lathe_on', 'lathe_off']
    else:
        categories = list(MESSAGES.keys())
    
    # Show config
    print("🎙️  Dust Collector Tool Announcement Generator")
    print(f"   Audio root: {AUDIO_ROOT}")
    print(f"   Tools: {args.tool}")
    print(f"   Voices: {len(VOICES)}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    # Count what needs to be generated
    to_generate = []
    to_skip = []
    
    for category in categories:
        messages = MESSAGES[category]
        output_dir = AUDIO_ROOT / category
        
        for idx, message in enumerate(messages, start=1):
            for voice_name, voice_id in VOICES.items():
                filename = f"{category}_{idx:03d}_{voice_name}.mp3"
                output_path = output_dir / filename
                
                if output_path.exists():
                    to_skip.append(output_path)
                else:
                    to_generate.append((category, idx, message, voice_name, voice_id, output_path))
    
    # Summary
    total = len(to_generate) + len(to_skip)
    print(f"📊 Status:")
    print(f"   Total files expected: {total}")
    print(f"   Already exist (skip): {len(to_skip)}")
    print(f"   Need to generate:     {len(to_generate)}")
    print()
    
    if not to_generate:
        print("✅ All files already exist! Nothing to do.")
        return
    
    if args.dry_run:
        print("🔍 Dry run - files that WOULD be generated:")
        for category, idx, message, voice_name, voice_id, output_path in to_generate[:20]:
            print(f"   {output_path.relative_to(PROJECT_ROOT)}")
            print(f"     Text: \"{message}\"")
        if len(to_generate) > 20:
            print(f"   ... and {len(to_generate) - 20} more")
        print()
        print(f"   Would generate {len(to_generate)} files using {len(VOICES)} voices")
        return
    
    # Estimate time
    est_seconds = len(to_generate) * (API_DELAY + 1.5)
    est_minutes = est_seconds / 60
    print(f"⏱️  Estimated time: ~{est_minutes:.0f} minutes")
    print()
    
    # Generate!
    generated = 0
    failed = 0
    
    for i, (category, idx, message, voice_name, voice_id, output_path) in enumerate(to_generate, 1):
        print(f"[{i}/{len(to_generate)}] {output_path.name}")
        print(f"   \"{message}\"")
        
        if generate_audio_file(message, voice_id, output_path, api_key):
            generated += 1
            print(f"   ✓ Saved to {output_path.relative_to(PROJECT_ROOT)}")
        else:
            failed += 1
        
        # Polite delay between API calls
        if i < len(to_generate):
            time.sleep(API_DELAY)
    
    # Final summary
    print()
    print("=" * 60)
    print(f"🎉 Generation complete!")
    print(f"   Generated: {generated}")
    print(f"   Skipped:   {len(to_skip)}")
    print(f"   Failed:    {failed}")
    print(f"   Output:    {AUDIO_ROOT}")
    print("=" * 60)
    
    if failed > 0:
        print(f"\n⚠️  {failed} files failed - run again to retry")


if __name__ == '__main__':
    main()
