#!/bin/bash
# Simple installation script for Analysis Toolkit
# Run from your DustCollectorSoftware directory

set -e  # Exit on any error

echo "🎯 Dust Collector Analysis Toolkit - Simple Installation"
echo ""

# Check we're in the right place
if [ ! -d "src" ]; then
    echo "❌ Error: Can't find src/ directory"
    echo "   Please run this script from your DustCollectorSoftware directory"
    echo ""
    echo "   cd ~/DustCollectorSoftware"
    echo "   ./INSTALL.sh"
    exit 1
fi

echo "✓ Found src/ directory"
echo ""

# Create analysis directory
echo "📁 Creating analysis/ directory..."
mkdir -p analysis/diagrams

# Move toolkit files into analysis/
echo "📦 Moving toolkit files into analysis/..."

for file in generate_diagrams.py Makefile diagrams_viewer.html VIEW_DIAGRAMS.sh README.md QUICK_REFERENCE.txt; do
    if [ -f "$file" ]; then
        mv "$file" analysis/
        echo "   ✓ Moved $file"
    else
        echo "   ⚠ Warning: $file not found (may already be moved)"
    fi
done

# Set permissions
echo ""
echo "🔧 Setting permissions..."
chmod +x analysis/generate_diagrams.py
chmod +x analysis/VIEW_DIAGRAMS.sh

# Migrate old diagrams if they exist
if [ -d "dust_collector_diagrams" ] && [ "$(ls -A dust_collector_diagrams/*.png 2>/dev/null)" ]; then
    echo ""
    echo "🔄 Found existing diagrams in dust_collector_diagrams/"
    cp dust_collector_diagrams/*.png analysis/diagrams/ 2>/dev/null || true
    echo "   ✓ Copied to analysis/diagrams/"
    echo "   (Original directory preserved - you can delete it later)"
fi

# Flatten nested AudioCoolness if it exists
if [ -d "AudioCoolness/AudioCoolness" ]; then
    echo ""
    echo "🔄 Flattening nested AudioCoolness directory..."
    if [ -d "AudioCoolness/AudioCoolness/safe" ]; then
        mv AudioCoolness/AudioCoolness/safe AudioCoolness/safe_temp
        echo "   ✓ Moved safe/"
    fi
    if [ -d "AudioCoolness/AudioCoolness/unsafe" ]; then
        mv AudioCoolness/AudioCoolness/unsafe AudioCoolness/unsafe_temp
        echo "   ✓ Moved unsafe/"
    fi
    rmdir AudioCoolness/AudioCoolness 2>/dev/null || rm -rf AudioCoolness/AudioCoolness
    [ -d "AudioCoolness/safe_temp" ] && mv AudioCoolness/safe_temp AudioCoolness/safe
    [ -d "AudioCoolness/unsafe_temp" ] && mv AudioCoolness/unsafe_temp AudioCoolness/unsafe
    echo "   ✓ Structure flattened"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Directory structure:"
echo "   DustCollectorSoftware/"
echo "   ├── analysis/              ← Your new toolkit"
echo "   │   ├── generate_diagrams.py"
echo "   │   ├── Makefile"
echo "   │   ├── diagrams_viewer.html"
echo "   │   ├── VIEW_DIAGRAMS.sh"
echo "   │   ├── README.md"
echo "   │   ├── QUICK_REFERENCE.txt"
echo "   │   └── diagrams/          ← Generated PNGs go here"
echo "   └── src/"
echo ""
echo "📚 Next steps:"
echo "   cd analysis"
echo "   make              # Generate all diagrams"
echo "   make view         # View in browser"
echo ""

# Ask about running make
read -p "Generate diagrams now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd analysis
    echo ""
    echo "🎨 Generating diagrams..."
    make all
    
    echo ""
    read -p "Open viewer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        make view
    fi
fi

echo ""
echo "🎉 All done!"
