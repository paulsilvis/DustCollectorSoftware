#!/bin/bash
# Reorganize AudioCoolness directory to clean, flat structure
# Run from DustCollectorSoftware root directory
#
# BEFORE:                          AFTER:
# AudioCoolness/                   AudioCoolness/
#   AudioCoolness/                   safe/
#     safe/                          unsafe/
#     unsafe/                        saw_on/
#     saw_on_*.mp3 (scattered)       saw_off/
#     saw_off_*.mp3                  lathe_on/
#     lathe_on_*.mp3                 lathe_off/
#     lathe_off_*.mp3

set -e

echo "🔧 AudioCoolness Directory Reorganization"
echo ""

# Verify we're in the right place
if [ ! -d "AudioCoolness" ] || [ ! -d "src" ]; then
    echo "❌ Error: Please run from your DustCollectorSoftware root directory"
    echo "   cd ~/DustCollectorSoftware"
    echo "   bash reorganize_audio.sh"
    exit 1
fi

AUDIO_ROOT="AudioCoolness"
INNER="AudioCoolness/AudioCoolness"

echo "📁 Current structure:"
tree -d AudioCoolness 2>/dev/null || ls -la AudioCoolness/
echo ""

# Create all target directories at the top level
echo "📁 Creating target directories..."
mkdir -p "$AUDIO_ROOT/safe"
mkdir -p "$AUDIO_ROOT/unsafe"
mkdir -p "$AUDIO_ROOT/saw_on"
mkdir -p "$AUDIO_ROOT/saw_off"
mkdir -p "$AUDIO_ROOT/lathe_on"
mkdir -p "$AUDIO_ROOT/lathe_off"
echo "   ✓ Directories created"
echo ""

# Move safe/ and unsafe/ if they're in the inner AudioCoolness
if [ -d "$INNER/safe" ]; then
    echo "🔄 Moving safe/ from inner directory..."
    count=$(ls "$INNER/safe" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        cp "$INNER/safe/"* "$AUDIO_ROOT/safe/" 2>/dev/null || true
        echo "   ✓ Moved $count files to AudioCoolness/safe/"
    else
        echo "   ⚠ safe/ was empty"
    fi
fi

if [ -d "$INNER/unsafe" ]; then
    echo "🔄 Moving unsafe/ from inner directory..."
    count=$(ls "$INNER/unsafe" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        cp "$INNER/unsafe/"* "$AUDIO_ROOT/unsafe/" 2>/dev/null || true
        echo "   ✓ Moved $count files to AudioCoolness/unsafe/"
    else
        echo "   ⚠ unsafe/ was empty"
    fi
fi

# Move any tool audio files that are scattered in the inner directory
if [ -d "$INNER" ]; then
    echo ""
    echo "🔄 Moving tool audio files from inner directory..."

    for category in saw_on saw_off lathe_on lathe_off; do
        count=$(ls "$INNER/${category}_"*.mp3 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            cp "$INNER/${category}_"*.mp3 "$AUDIO_ROOT/$category/" 2>/dev/null || true
            echo "   ✓ Moved $count ${category} files"
        fi
    done

    # Check for any other mp3 files in the inner directory
    other=$(ls "$INNER"/*.mp3 2>/dev/null | grep -v safe | grep -v unsafe | wc -l)
    if [ "$other" -gt 0 ]; then
        echo ""
        echo "   ⚠ Found $other unrecognized mp3 files in $INNER:"
        ls "$INNER"/*.mp3 2>/dev/null | head -5
        echo "   These were NOT moved - please handle manually"
    fi
fi

# Also check the top-level AudioCoolness for any stray tool audio files
echo ""
echo "🔄 Checking for stray tool audio files at top level..."
for category in saw_on saw_off lathe_on lathe_off; do
    count=$(ls "$AUDIO_ROOT/${category}_"*.mp3 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        mv "$AUDIO_ROOT/${category}_"*.mp3 "$AUDIO_ROOT/$category/" 2>/dev/null || true
        echo "   ✓ Moved $count stray ${category} files"
    fi
done

echo ""
echo "📊 Final counts:"
for dir in safe unsafe saw_on saw_off lathe_on lathe_off; do
    count=$(ls "$AUDIO_ROOT/$dir" 2>/dev/null | wc -l)
    echo "   $dir/: $count files"
done

echo ""
echo "✅ Reorganization complete!"
echo ""
echo "📁 New structure:"
tree -d AudioCoolness 2>/dev/null || ls -la AudioCoolness/
echo ""
echo "⚠️  BEFORE DELETING OLD DIRECTORY:"
echo "   1. Verify the counts above look right"
echo "   2. Test that your code still works"
echo "   3. Then remove the nested directory:"
echo "      rm -rf AudioCoolness/AudioCoolness"
echo ""
echo "📝 THEN COMMIT:"
echo "   git add AudioCoolness/"
echo "   git commit -m 'Reorganize AudioCoolness: flat structure with tool-specific dirs'"
echo "   git push"
