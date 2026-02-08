# ElevenLabs Audio Announcements for Dust Collector AQM

**COSMIC AUDIO SYSTEM** 🚀🎤

This system generates high-quality, randomly-selected voice announcements for your air quality monitoring system using ElevenLabs text-to-speech.

**What makes this awesome:**
- 20 different messages for "unsafe air" 
- 20 different messages for "safe air"
- 10 different voices for each category
- **400 total unique announcements** (20 × 10 × 2)
- Mix of male/female, professional/casual, urgent/calm voices
- Random selection = visitors will be surprised every time!

---

## 📁 Files in This System

```
DustCollectorSoftware/
├── AudioCoolness/              # Generated audio files (created after running generator)
│   ├── unsafe/                 # 200 unsafe announcement variations
│   │   ├── unsafe_josh_001.mp3
│   │   ├── unsafe_josh_002.mp3
│   │   └── ... (200 files total)
│   ├── safe/                   # 200 safe announcement variations  
│   │   ├── safe_adam_001.mp3
│   │   ├── safe_adam_002.mp3
│   │   └── ... (200 files total)
│   └── manifest.json           # Auto-generated file index
│
├── announcement_config.yaml    # Master configuration (edit this!)
├── generate_announcements.py  # Script to generate all audio files
├── preview_announcements.py   # Tool to listen/test/curate
├── aqm_announcer_elevenlabs.py # Modified announcer module
└── README.md                   # This file
```

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies

```bash
# Python packages
pip install elevenlabs pyyaml

# Audio player (choose one)
sudo apt-get install mpg123        # Recommended
# OR
sudo apt-get install alsa-utils     # For aplay
# OR  
pip install pygame                  # For Python-based playback
```

### Step 2: Get ElevenLabs API Key

1. Go to https://elevenlabs.io/
2. Sign up for free account (10,000 characters/month free)
3. Get your API key from Settings → API Keys
4. Set environment variable:

```bash
export ELEVENLABS_API_KEY="your_key_here"

# To make it permanent, add to ~/.bashrc:
echo 'export ELEVENLABS_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Review/Edit Configuration

Open `announcement_config.yaml` and customize:
- Messages (add/remove/edit the 20 messages per category)
- Voice settings (adjust stability, style for each voice)
- Output directory

**The default config is ready to use!** But feel free to customize.

### Step 4: Generate Audio Files

```bash
# This will create all 400 audio files
python generate_announcements.py

# This may take 10-15 minutes to complete
# Progress is shown for each file
```

**What happens:**
- Creates `AudioCoolness/unsafe/` with 200 files
- Creates `AudioCoolness/safe/` with 200 files  
- Shows progress for each file generated
- Creates manifest.json for tracking

**Cost:** Uses ~8,000 characters from your 10,000/month free tier.

### Step 5: Preview & Test

```bash
# Interactive menu to listen to samples
python preview_announcements.py

# Or play random samples from command line
python preview_announcements.py --random 5

# List all generated files
python preview_announcements.py --list
```

**Preview menu options:**
1. Show summary (file counts, sizes, voices)
2. Play random samples
3. Play ALL unsafe announcements
4. Play ALL safe announcements  
5. Play specific voice
6. Test announcer integration
7. Delete unwanted files

**Tip:** Listen to samples and delete any voices you don't like!

### Step 6: Integrate with Your System

**Option A: Replace your existing announcer**

1. Backup your current `aqm_announcer.py`
2. Replace the `_Announcer` class with the one from `aqm_announcer_elevenlabs.py`
3. Update your config:

```yaml
announce:
  enabled: true
  audio_dir: "AudioCoolness"  # or full path
  player: "mpg123"            # or "aplay" or "pygame"
  min_seconds_between: 60.0
```

**Option B: Use as separate module**

Import and use directly:

```python
from aqm_announcer_elevenlabs import run_aqm_announcer

# In your event loop
await run_aqm_announcer(event_bus, config)
```

### Step 7: Test End-to-End

```bash
# Standalone test of announcer
python aqm_announcer_elevenlabs.py AudioCoolness

# This will play one unsafe and one safe announcement
```

---

## 🎛️ Configuration Reference

### Voice Selection Strategy

**UNSAFE (Alert/Warning) Voices:**
- **Josh** - Deep authoritative male, commanding
- **Callum** - Dramatic intense male, movie trailer
- **Adam** - Professional urgent male
- **Clyde** - Blue collar rough male  
- **Arnold** - Assertive male, Eastern European
- **Serena** - Sultry provocative female
- **Elli** - Expressive dramatic female
- **Charlotte** - Professional female authority
- **Lily** - Young concerned female (for granddaughters!)
- **Freya** - Strong confident female, slight accent

**SAFE (All Clear) Voices:**
- **Adam** - Warm professional male
- **Antoni** - Balanced clear male
- **Charlie** - Friendly casual male
- **Sam** - Reassuring blue collar male
- **Charlotte** - Soothing calm female
- **Bella** - Soft reassuring female
- **Rachel** - Calm narrative female
- **Matilda** - Warm young cheerful female (granddaughter voice!)
- **Dorothy** - Pleasant young British female
- **Grace** - Gentle mature reassuring female

### Voice Parameters Explained

```yaml
stability: 0.3        # 0.0-1.0: Lower = more expressive, Higher = more consistent
similarity_boost: 0.8 # 0.0-1.0: How closely to match original voice
style: 0.5           # 0.0-1.0: Amount of stylistic exaggeration
```

**For urgent warnings:** Low stability (0.2-0.4) = dramatic inflection
**For calm messages:** High stability (0.7-0.9) = steady, measured tone

---

## 📊 Storage & Performance

**Generated Files:**
- 400 MP3 files @ ~50-100 KB each
- Total size: ~20-40 MB
- **Your 250GB SSD:** Less than 0.02% used! 😎

**Playback:**
- No internet required (files are local)
- No API calls at runtime (zero cost!)
- Instant playback (pre-generated)
- 100% reliable even if internet is down

**Generation Time:**
- ~400 files @ 0.5-1 second each
- Total: 10-15 minutes one-time
- You only regenerate if you want to change messages/voices

---

## 🎨 Customization Ideas

### More Messages

Edit `announcement_config.yaml` and add more messages:

```yaml
unsafe_messages:
  - "Warning! Microscopic ninja dust detected!"
  - "Alert! The air has gone rogue!"
  # ... add as many as you want
```

Then regenerate:
```bash
python generate_announcements.py --regenerate
```

### Different Voices per Time of Day

Create multiple configs and swap them:

```yaml
# morning_config.yaml - cheerful voices
# evening_config.yaml - calm voices  
# night_config.yaml - quiet voices
```

### Sound Effects

Add alarm sounds before announcements:

1. Download alarm/siren MP3s
2. Play before the announcement in `_speak()` method
3. Example: `BEEP BEEP BEEP` then voice announcement

### Seasonal Variations

Generate themed sets:
- Christmas voices (ho ho ho!)
- Halloween spooky voices
- Summer beach vibes
- Winter cozy tones

**With 250GB, you could have THOUSANDS of variations!**

---

## 🐛 Troubleshooting

### "No audio files found"
- Run `generate_announcements.py` first
- Check that `AudioCoolness/unsafe/` and `AudioCoolness/safe/` exist
- Verify files with: `ls -lh AudioCoolness/unsafe/`

### "mpg123 not found"
```bash
sudo apt-get install mpg123
```

### "API key not set"
```bash
export ELEVENLABS_API_KEY="your_key_here"
```

### Files generated but no sound
- Check speaker volume
- Test manually: `mpg123 AudioCoolness/unsafe/unsafe_josh_001.mp3`
- Try different player: change `player: "aplay"` in config

### Rate limiting errors during generation
- Free tier: 10,000 chars/month
- If you hit limit, wait until next month or upgrade
- Alternative: Generate in batches, comment out some voices

### Voice sounds wrong
- Regenerate with different `stability` setting
- Try different voice from ElevenLabs library
- Delete unwanted files manually

---

## 🎓 Advanced Usage

### Test Announcer Standalone

```python
python -c "
import asyncio
from aqm_announcer_elevenlabs import _Announcer

async def test():
    a = _Announcer('AudioCoolness', 'mpg123')
    await a._speak(is_unsafe=True)   # Play unsafe
    await a._speak(is_unsafe=False)  # Play safe
    
asyncio.run(test())
"
```

### Get List of All ElevenLabs Voices

```python
from elevenlabs import voices

all_voices = voices()
for v in all_voices:
    print(f"{v.name}: {v.voice_id}")
    print(f"  Labels: {v.labels}")
```

### Regenerate Specific Category Only

Edit the generator script to skip one category, or delete files and run with `--regenerate`.

### Export Manifest

The `manifest.json` file contains:
- Generation timestamp
- File counts
- Complete file listing

Use for documentation or backup tracking.

---

## 📝 Integration Checklist

- [ ] Install Python dependencies (`elevenlabs`, `pyyaml`)
- [ ] Install audio player (`mpg123`)
- [ ] Get ElevenLabs API key
- [ ] Set `ELEVENLABS_API_KEY` environment variable
- [ ] Review/customize `announcement_config.yaml`
- [ ] Run `generate_announcements.py` (generates 400 files)
- [ ] Run `preview_announcements.py` to test
- [ ] Delete any voices you don't like
- [ ] Update your config to point to `AudioCoolness/`
- [ ] Replace/import `aqm_announcer_elevenlabs.py` module
- [ ] Test end-to-end with dust collector
- [ ] Enjoy cosmic audio! 🎤

---

## 💡 Pro Tips

1. **Start with defaults** - The provided config is battle-tested
2. **Preview before deploying** - Listen to samples first
3. **Delete liberally** - Remove voices/messages you don't like
4. **Keep backups** - Save your favorite config versions
5. **Mix it up** - Regenerate occasionally with new messages
6. **Go wild** - With 250GB, you have infinite room to experiment!

---

## 🎉 What Your Visitors Will Experience

**First time:** 
"Warning! Unsafe particulate matter detected..." (Deep male voice)

**Second time:**
"Yo! Air quality tanked. Scrubber's on it, boss." (Casual voice)

**Third time:**  
"Alert! Microscopic particles detected..." (Sultry female voice)

**Their reaction:**
"Wait, did the voice just change?!" 🤯

---

## 📚 Further Resources

- ElevenLabs Documentation: https://elevenlabs.io/docs
- Voice Library: https://elevenlabs.io/voice-library
- API Pricing: https://elevenlabs.io/pricing
- Python SDK: https://github.com/elevenlabs/elevenlabs-python

---

## 🙏 Credits

**Created for:** An awesome workshop with a cosmic dust collection system
**Powered by:** ElevenLabs AI voice synthesis
**Storage:** 250GB SSD (barely used!)
**Approved by:** Future granddaughters who will hear their voices

---

**Have fun and stay safe! The air quality police are watching... and talking!** 👮‍♀️🎤
