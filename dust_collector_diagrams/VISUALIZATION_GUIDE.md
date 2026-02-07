# Dust Collector System Visualization Suite

## 🎨 What's Included

This package contains multiple visualization tools for your dust collector system:

### 1. **Automated Analyzers** (Python Scripts)
- `analyze_events.py` - Scans your codebase and extracts event flow patterns
- `generate_enhanced_diagrams.py` - Creates beautiful, hand-crafted diagrams

### 2. **Six Different Diagram Styles**

#### A. **System Diagram Enhanced** ⭐ BEST FOR SHOP DISPLAY
- `system_diagram_enhanced.png/svg` - Full color architectural overview
- `system_diagram_poster.png` - High-res version (300 DPI, 735KB) for printing
- Shows event bus, hardware, control tasks, event flow
- **Use this one** for your main shop display!

#### B. **Data Flow Diagram**
- `dataflow_diagram.png/svg` - How signals flow from sensors to outputs
- Great for explaining "how it works" to visitors

#### C. **State Machine Diagram**
- `state_machine.png/svg` - Gate controller logic
- Shows the states and transitions with timings

#### D. **Event Flow Diagram** (Auto-generated)
- `event_flow.png/svg` - Who publishes/subscribes to what
- Extracted directly from your code

#### E. **Component Architecture** (Auto-generated)
- `component_architecture.png/svg` - Layered architecture view
- Shows hardware, tasks, and dependencies

#### F. **Module Dependencies** (Auto-generated)
- `module_dependencies.png/svg` - Python module structure
- Useful for code maintenance

### 3. **Interactive HTML Viewer**
- `diagrams_viewer.html` - Beautiful web page showing all diagrams
- Click to zoom, download links for each diagram
- Can be displayed on a tablet/monitor in your shop!

### 4. **Generation Scripts**
- `generate_all_pngs.sh` - Regenerate all PNG files
- `generate_all_svgs.sh` - Regenerate all SVG files

### 5. **Documentation**
- `DIAGRAMS_README.md` - Comprehensive guide to all diagrams
- Explains what each diagram shows and how to customize

## 🚀 Quick Start

### For Shop Display

**Option 1: Print the Poster**
```bash
# Use the high-resolution poster version (300 DPI)
# Print: system_diagram_poster.png
# Recommended size: 24"x36" or larger
```

**Option 2: Digital Display**
```bash
# Open diagrams_viewer.html in a browser on a tablet/monitor
# Full-screen it (F11) for a kiosk-style display
firefox diagrams_viewer.html &
```

**Option 3: Multiple Prints**
```bash
# Print several diagrams and create a poster board:
# - system_diagram_enhanced.png (main)
# - dataflow_diagram.png (how it works)
# - state_machine.png (detail view)
```

### Regenerating Diagrams

If you update your code and want fresh diagrams:

```bash
# 1. Analyze the codebase
python3 analyze_events.py

# 2. Generate enhanced diagrams
python3 generate_enhanced_diagrams.py

# 3. Create image files
./generate_all_pngs.sh
./generate_all_svgs.sh

# 4. Optional: High-res poster
dot -Tpng -Gdpi=300 system_diagram_enhanced.dot -o system_diagram_poster.png
```

## 🎯 Recommendations for Shop Eye-Candy

### Best Standalone Display
**System Diagram Enhanced** (`system_diagram_enhanced.png`)
- Most comprehensive
- Best colors and layout
- Shows everything: hardware, events, controllers

### Best Explanation Sequence
1. **Data Flow** - "Here's how the system detects tools and controls gates"
2. **System Diagram** - "Here's the complete architecture"
3. **State Machine** - "Here's the detailed gate logic"

### For a Tablet/Monitor
- Use `diagrams_viewer.html`
- Set to auto-refresh or slideshow mode
- Visitors can tap to zoom

## 🎨 Customization Ideas

### Change Colors
Edit `generate_enhanced_diagrams.py` and modify the `fillcolor` values:
```python
fillcolor="#FF6B6B:#C92A2A"  # Gradient red
fillcolor="#66BB6A"           # Solid green
```

### Add Your Logo
Add to the DOT file:
```dot
// In the graph attributes section
label=<<TABLE BORDER="0">
  <TR><TD><IMG SRC="logo.png"/></TD></TR>
  <TR><TD>Dust Collector System</TD></TR>
</TABLE>>;
```

### Annotate Code for Better Auto-Generation
Add structured comments:
```python
# @publishes: saw.on, saw.off
# @subscribes: collector.state
# @hardware: PCF8574 @ I2C 0x21
```

Then extend the analyzer to parse these.

## 📊 File Formats Explained

### PNG vs SVG
- **PNG**: Raster image, fixed size, good for printing
  - Use for: Posters, printed documentation
  - Pro: Widely compatible
  - Con: Pixelated when zoomed

- **SVG**: Vector image, infinite zoom, small file size
  - Use for: Web display, interactive viewers
  - Pro: Perfect zoom, editable
  - Con: Not all printers handle SVG well

### Which Format When?
- **Print → PNG** (especially the 300 DPI poster version)
- **Web/Monitor → SVG** (crisp at any size)
- **Documentation → Both** (PNG for PDF, SVG for HTML)

## 🔧 Technical Details

### Dependencies
- Python 3 (for analyzers)
- Graphviz (for DOT → PNG/SVG conversion)

### Install Graphviz
```bash
# Debian/Ubuntu
sudo apt-get install graphviz

# macOS
brew install graphviz

# Or just use an online converter
# Upload .dot files to: https://dreampuf.github.io/GraphvizOnline/
```

### Diagram Sizes
- Event Flow: 136 KB (PNG), 18 KB (SVG)
- System Enhanced: 194 KB (PNG), 25 KB (SVG)
- Poster Version: 735 KB (300 DPI PNG)

## 💡 More Ideas

### Animated Diagrams
The SVG files can be enhanced with CSS animations:
- Pulse effect on event nodes when active
- Animated data flow along edges
- Color changes based on system state

### Live Integration
Create a version that shows real-time system status:
- Green/red indicators for gates
- Event counters
- Last event timestamp

### QR Code
Add a QR code to printed diagrams linking to:
- Live system dashboard
- This documentation
- GitHub repository

## 📝 License & Credits

Generated using:
- Python AST parsing
- Graphviz DOT language
- Custom visualization scripts

Created for: Your dust collector control system
Date: February 2026

---

**Pro Tip**: The system_diagram_poster.png at 300 DPI will look amazing at 24"x36" or even larger. Most print shops can handle this size easily!
