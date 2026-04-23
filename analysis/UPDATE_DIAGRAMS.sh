#!/bin/bash
# Quick update script for improved diagram layouts
# Run this in your DustCollectorSoftware directory

echo "🔧 Updating diagram generator with improved layouts..."

if [ ! -f "generate_diagrams.py" ]; then
    echo "❌ Error: generate_diagrams.py not found in current directory"
    echo "   Please run this from the directory containing the downloaded file"
    exit 1
fi

if [ ! -d "analysis" ]; then
    echo "❌ Error: analysis/ directory not found"
    echo "   Make sure you're in the DustCollectorSoftware directory"
    exit 1
fi

# Backup the old version
if [ -f "analysis/generate_diagrams.py" ]; then
    echo "📦 Backing up old version to analysis/generate_diagrams.py.bak"
    cp analysis/generate_diagrams.py analysis/generate_diagrams.py.bak
fi

# Copy new version
echo "📋 Installing updated generator..."
cp generate_diagrams.py analysis/
chmod +x analysis/generate_diagrams.py

echo ""
echo "✅ Update complete!"
echo ""
echo "Regenerate the fixed diagrams:"
echo "   cd analysis"
echo "   make components modules"
echo "   make view"
echo ""
