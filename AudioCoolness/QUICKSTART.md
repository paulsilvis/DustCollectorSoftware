# QUICK START - Get Running in 5 Minutes! ⚡

Too excited to read the full README? Here's the express lane:

## 1. Install (30 seconds)
```bash
bash setup.sh
```

## 2. Get API Key (2 minutes)
1. Go to https://elevenlabs.io/
2. Sign up (free!)
3. Copy your API key from Settings
4. Run:
```bash
export ELEVENLABS_API_KEY="paste_your_key_here"
```

## 3. Generate Audio (10 minutes)
```bash
python3 generate_announcements.py
```
*Grab coffee while it generates 400 files*

## 4. Test It! (1 minute)
```bash
python3 preview_announcements.py --random 3
```

## 5. Integrate (2 minutes)
Update your config:
```yaml
announce:
  enabled: true
  audio_dir: "AudioCoolness"
  player: "mpg123"
```

## Done! 🎉

Your dust collector now has:
- 200 unique "unsafe air" announcements
- 200 unique "safe air" announcements  
- 10 different voices
- Random selection = endless variety!

---

**Want details?** Read the full README.md

**Got problems?** Check the Troubleshooting section in README.md

**Want to customize?** Edit announcement_config.yaml and regenerate

**Ready to blow minds?** Just wait until visitors hear the different voices! 😎
