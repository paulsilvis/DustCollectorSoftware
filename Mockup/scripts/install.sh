#!/usr/bin/env bash
set -euo pipefail
sudo cp system/dustcollector.service /etc/systemd/system/
sudo systemctl daemon-reload
echo "Service installed. Enable with: sudo systemctl enable --now dustcollector"
