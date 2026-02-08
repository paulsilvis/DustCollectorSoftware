#!/bin/bash
#
# ElevenLabs Audio Announcement System - Setup Script
#
# This script automates the installation and setup process.
# Run with: bash setup.sh
#

set -e  # Exit on error

echo "=========================================="
echo "ElevenLabs Audio Announcement Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✓ Python packages installed"
echo ""

# Install audio player
echo "Checking for audio player..."
if command -v mpg123 &> /dev/null; then
    echo "✓ mpg123 already installed"
else
    echo "Installing mpg123..."
    sudo apt-get update
    sudo apt-get install -y mpg123
    echo "✓ mpg123 installed"
fi
echo ""

# Check for API key
echo "Checking ElevenLabs API key..."
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "⚠ WARNING: ELEVENLABS_API_KEY not set!"
    echo ""
    echo "You need to set your API key:"
    echo "  1. Get key from: https://elevenlabs.io/"
    echo "  2. Set environment variable:"
    echo "     export ELEVENLABS_API_KEY='your_key_here'"
    echo ""
    echo "  3. Make it permanent (add to ~/.bashrc):"
    echo "     echo 'export ELEVENLABS_API_KEY=\"your_key_here\"' >> ~/.bashrc"
    echo "     source ~/.bashrc"
    echo ""
else
    echo "✓ API key found (ends with: ...${ELEVENLABS_API_KEY: -8})"
fi
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x generate_announcements.py
chmod +x preview_announcements.py
echo "✓ Scripts are executable"
echo ""

# Summary
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Set your API key (if not already done)"
echo "  2. Review announcement_config.yaml"
echo "  3. Run: python3 generate_announcements.py"
echo "  4. Test: python3 preview_announcements.py"
echo ""
echo "For detailed instructions, see README.md"
echo ""
