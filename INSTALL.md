# ISS Feed Service - Installation Instructions

## What This Does

This service displays a live 24/7 ISS Earth view from Sen's YouTube channel on your Dell monitor (HDMI-0). It starts automatically at boot and runs continuously in the background.

## Prerequisites

1. Install mpv and yt-dlp:
   ```bash
   sudo apt update
   sudo apt install mpv yt-dlp
   ```

2. Ensure the graphical desktop is set to auto-start:
   ```bash
   # This should already be configured from earlier setup
   systemctl get-default
   # Should show: graphical.target
   ```

## Installation Steps

1. Copy the stream script to the system:
   ```bash
   sudo cp iss-stream.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/iss-stream.sh
   ```

2. Create the log file with proper permissions:
   ```bash
   sudo touch /var/log/iss-feed.log
   sudo chown paul:paul /var/log/iss-feed.log
   ```

3. Copy the service file:
   ```bash
   sudo cp iss-feed.service /etc/systemd/system/
   ```

4. Copy the control script:
   ```bash
   sudo cp iss /usr/local/bin/
   sudo chmod +x /usr/local/bin/iss
   ```

5. Reload systemd and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable iss-feed.service
   ```

6. Start the service:
   ```bash
   iss start
   ```

## Usage

After installation, use these simple commands:

- `iss start` - Start the ISS feed
- `iss stop` - Stop the ISS feed
- `iss restart` - Restart the ISS feed
- `iss status` - Check if it's running
- `iss logs` - View recent log entries
- `iss tail` - Watch logs in real-time

## Troubleshooting

### Stream Won't Start

Check the logs:
```bash
iss logs
```

Common issues:
- Network not ready: The service waits 10 seconds after boot, but you can increase this in the service file
- Desktop not started: Make sure graphical.target is enabled
- YouTube stream changed: Sen's stream is very stable, but if it changes, update STREAM_URL in the script

### Checking Service Status

```bash
systemctl status iss-feed.service
```

Or just:
```bash
iss status
```

### Viewing Full Logs

```bash
journalctl -u iss-feed.service --no-pager
```

Or:
```bash
iss logs
```

### Video Performance Issues

The stream is 1920x1080 which matches your Dell monitor. If you experience lag:
- The service already uses `--profile=fast` and `--hwdec=auto` for best performance
- Check system load: `htop`
- The Pi 4 with 16GB RAM should handle this easily

### Disabling Audio

Audio is enabled by default. To disable it, edit `/usr/local/bin/iss-stream.sh` and add `--no-audio` to the mpv command.

## Notes

- The service runs as user 'paul'
- The stream displays on your Dell monitor (HDMI-0) 
- It auto-restarts if it crashes (RestartSec=30)
- It auto-retries if the stream connection drops
- Logs are written to /var/log/iss-feed.log and systemd journal
- The service starts automatically on boot after the graphical desktop loads

## About the Stream

This service uses Sen's 24/7 ISS livestream from YouTube (youtube.com/@sen). Sen provides free 4K Earth views from the International Space Station. The ISS orbits Earth every 90 minutes, so you'll see sunrise/sunset every 45 minutes. When the ISS is on the dark side of Earth, you'll see city lights and occasional lightning.
