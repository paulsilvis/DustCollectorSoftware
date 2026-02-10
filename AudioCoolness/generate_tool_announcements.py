#!/usr/bin/env python3
"""
Generate audio announcements for tool on/off events.
Creates 800 files total: 20 messages × 2 states × 2 tools × 10 voices
"""

import os
import requests
from pathlib import Path

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")

# Voice IDs (same as AQM announcements)
VOICES = {
    'rachel': '21m00Tcm4TlvDq8ikWAM',
    'clyde': '2EiwWnXFnvU5JabPnv8n',
    'domi': 'AZnzlk1XvdvUeBnXmlld',
    'fin': 'D38z5RcWu1voky8WS1ja',
    'jessica': 'cgSgspJ2msm6clMCkdW9',
    'eric': 'cjVigY5qzO86Huf0OWal',
    'drew': 'jsCqWAovK2LkecY7zXl4',
    'lily': 'pFZP5JQG7iQjIQuC4Bku',
    'adam': 'pNInz6obpgDQGcFmaJgB',
    'bill': 'pqHfZKP75CvOlQylNhV4'
}

# Output directory
OUTPUT_DIR = Path('AudioCoolness')

# Message pools for each tool/state combination
MESSAGES = {
    'saw_on': [
        "Table saw activated",
        "Saw is running",
        "Let's make some cuts",
        "Saw on - keep those hands clear",
        "Cutting time - remember your push stick",
        "Saw spinning up - safety first",
        "Time to rip some wood",
        "Blade is hot - stay focused",
        "Let's turn wood into smaller wood",
        "Saw on - measure twice, cut once",
        "Alright, let's make some sawdust",
        "Ready to cut - push stick handy?",
        "Saw running - no loose clothing please",
        "Time to transform this lumber",
        "Blade spinning - respect the tool",
        "Let's do this safely",
        "Saw active - eye protection on?",
        "Ready for precision cutting",
        "The saw is yours - make it count",
        "Cutting mode engaged"
    ],
    
    'saw_off': [
        "Table saw stopped",
        "Saw is off",
        "Cutting complete",
        "Nice work - all fingers accounted for?",
        "Good job keeping it safe",
        "And we're done",
        "Another successful cut",
        "Blade stopped - well done",
        "Safe shutdown complete",
        "That's a wrap on the saw",
        "Clean cuts achieved",
        "Excellent work at the saw",
        "Saw off - time to check your work",
        "Mission accomplished",
        "Nice cutting session",
        "Saw secured - great job",
        "Another one in the books",
        "Perfect - saw is off",
        "Good cutting - stay sharp",
        "Saw down safely"
    ],
    
    'lathe_on': [
        "Lathe is spinning",
        "Lathe activated",
        "Time to turn",
        "Lathe on - secure your workpiece",
        "Let's make some turnings",
        "Spinning up the lathe",
        "Lathe running - goggles on?",
        "Ready to shape some wood",
        "Lathe engaged - tool rest set?",
        "Time for some turning magic",
        "Let's make the chips fly",
        "Lathe is live - stay alert",
        "Turning time - check your speed",
        "The lathe is all yours",
        "Ready to create something round",
        "Lathe spinning - hand position good?",
        "Let's turn this into art",
        "Active lathe - sharp tools ready?",
        "Spinning wood mode activated",
        "Lathe on - make something beautiful"
    ],
    
    'lathe_off': [
        "Lathe stopped",
        "Lathe is off",
        "Turning complete",
        "Nice work on the lathe",
        "Smooth finish achieved",
        "Lathe secured - well done",
        "Another beautiful turning",
        "Spindle stopped safely",
        "That's a wrap on the lathe",
        "Excellent turning session",
        "Lathe off - admire your work",
        "Clean shutdown complete",
        "Perfect - lathe is down",
        "Great work at the lathe",
        "Turning finished successfully",
        "Lathe secured - nice job",
        "Another one completed",
        "Spindle stopped - check for smoothness",
        "Beautiful work today",
        "Lathe down - well crafted"
    ]
}

def generate_audio_file(text: str, voice_id: str, output_path: Path):
    """Generate a single audio file using ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print(f"Error generating {output_path}: {response.status_code} - {response.text}")
        return False

def main():
    """Generate all tool announcement audio files."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_files = 0
    successful = 0
    failed = 0
    
    # Calculate total for progress tracking
    total_expected = len(MESSAGES) * 20 * len(VOICES)
    
    print(f"Generating {total_expected} audio files...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Generate files for each tool/state combination
    for tool_state, messages in MESSAGES.items():
        tool, state = tool_state.split('_')
        
        for idx, message in enumerate(messages, start=1):
            for voice_name, voice_id in VOICES.items():
                # Construct filename: saw_on_001_rachel.mp3
                filename = f"{tool}_{state}_{idx:03d}_{voice_name}.mp3"
                output_path = OUTPUT_DIR / filename
                
                total_files += 1
                
                # Skip if file already exists
                if output_path.exists():
                    print(f"[{total_files}/{total_expected}] Skipping (exists): {filename}")
                    successful += 1
                    continue
                
                # Generate the audio file
                print(f"[{total_files}/{total_expected}] Generating: {filename}")
                if generate_audio_file(message, voice_id, output_path):
                    successful += 1
                else:
                    failed += 1
    
    # Summary
    print()
    print("=" * 60)
    print(f"Generation complete!")
    print(f"Total files: {total_files}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
