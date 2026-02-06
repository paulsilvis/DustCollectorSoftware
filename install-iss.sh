#!/bin/bash

# Quick ISS Feed Service Installation Script
# Run this as your normal user (paul), not root

echo "=== ISS Feed Service Quick Installer ==="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "ERROR: Please run as normal user (paul), not root"
   exit 1
fi

# Install prerequisites
echo "Step 1: Installing mpv and yt-dlp..."
sudo apt update
sudo apt install -y mpv yt-dlp

# Copy stream script
echo ""
echo "Step 2: Installing stream script..."
sudo cp iss-stream.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/iss-stream.sh

# Create log file
echo ""
echo "Step 3: Creating log file..."
sudo touch /var/log/iss-feed.log
sudo chown paul:paul /var/log/iss-feed.log

# Copy service file
echo ""
echo "Step 4: Installing systemd service..."
sudo cp iss-feed.service /etc/systemd/system/

# Copy control script
echo ""
echo "Step 5: Installing control script..."
sudo cp iss /usr/local/bin/
sudo chmod +x /usr/local/bin/iss

# Reload and enable service
echo ""
echo "Step 6: Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable iss-feed.service

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "To start the ISS feed now: iss start"
echo "To check status: iss status"
echo "To view logs: iss logs"
echo ""
echo "The service will auto-start on next boot."
