#!/bin/bash

# ISS Live Stream Script using Sen's YouTube feed
# Displays on primary monitor (Dell HDMI-0)

# Sen's 24/7 ISS Earth viewing stream on YouTube
STREAM_URL="https://www.youtube.com/@sen/live"

# Log file
LOG_FILE="/var/log/iss-feed.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "Starting ISS stream from Sen YouTube channel..."

# Check if mpv and yt-dlp are available
if ! command -v mpv &> /dev/null; then
    log_message "ERROR: mpv not found. Please install mpv."
    exit 1
fi

if ! command -v yt-dlp &> /dev/null; then
    log_message "ERROR: yt-dlp not found. Please install yt-dlp."
    exit 1
fi

log_message "Using MPV player with yt-dlp for YouTube stream"

# MPV command with YouTube stream
# --fullscreen: run fullscreen
# --no-audio: disable audio (comment out if you want sound)
# --profile=fast: use faster decoding for better performance
# --hwdec=auto: hardware decoding if available
mpv --fullscreen \
    --profile=fast \
    --hwdec=auto \
    "$STREAM_URL" 2>&1 | while read line; do
    log_message "MPV: $line"
done
