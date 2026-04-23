# Dust Collector System Analysis Toolkit

Professional code analysis and architecture visualization for the event-driven dust collector control system.

## 📁 Directory Structure

```
analysis/
├── generate_diagrams.py     # Main diagram generator
├── Makefile                  # Build automation
├── diagrams_viewer.html      # Web-based diagram viewer
├── VIEW_DIAGRAMS.sh          # Quick viewer launcher
├── README.md                 # This file
└── diagrams/                 # Generated diagrams (auto-created)
    ├── system_diagram_enhanced.png
    ├── system_diagram_poster.png (300 DPI)
    ├── dataflow_diagram.png
    ├── state_machine.png
    ├── event_flow.png
    ├── component_architecture.png
    └── module_dependencies.png
```

## 🚀 Quick Start

### Generate All Diagrams
```bash
make
```

### Generate Specific Diagram
```bash
make architecture     # System architecture only
make events          # Event flow only
make dataflow        # Data flow only
```

### View Diagrams
```bash
make view            # Opens browser viewer
# OR
./VIEW_DIAGRAMS.sh   # Direct script
```

### Clean Up
```bash
make clean           # Remove all generated diagrams
```

## 📊 Available Diagrams

### 1. System Architecture (`architecture`)
**Files:** `system_diagram_enhanced.png` (150 DPI), `system_diagram_poster.png` (300 DPI)

Complete system overview showing:
- Event Bus (central pub/sub coordinator)
- Hardware Abstraction Layer (tools, gates, fans, sensors)
- Control Tasks (monitors and controllers)
- I²C bus connections
- Event flow between components

**Use case:** Understanding overall system design, explaining to others, documentation

---

### 2. Data Flow (`dataflow`)
**File:** `dataflow_diagram.png`

Shows how data moves through the system:
- Sensor readings (current sensors, air quality)
- Signal processing (ADC, threshold detection, debouncing)
- Event publication
- Control logic (gate/fan state machines)
- Actuator control (servos, relays)

**Use case:** Debugging signal path, understanding latency, optimizing performance

---

### 3. State Machine (`statemachine`)
**File:** `state_machine.png`

Gate control state machine:
- States: CLOSED → OPENING → OPEN → CLOSING → CLOSED
- Transitions triggered by tool events and servo completion
- Self-loops for stable states

**Use case:** Understanding gate behavior, debugging timing issues, documenting control logic

---

### 4. Event Flow (`events`)
**File:** `event_flow.png`

Publish/subscribe relationships:
- Publishers (which modules publish events)
- Events (message types)
- Subscribers (which modules listen)
- Connections showing data flow

**Use case:** Understanding event coupling, finding who uses what events, refactoring

---

### 5. Component Architecture (`components`)
**File:** `component_architecture.png`

Layered architecture view:
- Hardware Layer (device abstractions)
- Tasks Layer (control logic)
- Utility Layer (shared services)
- Dependencies between layers

**Use case:** Understanding system layers, planning refactoring, ensuring proper separation

---

### 6. Module Dependencies (`modules`)
**File:** `module_dependencies.png`

Python module import graph:
- All Python modules in src/
- Import relationships
- Color-coded by layer

**Use case:** Finding circular dependencies, understanding coupling, planning module splits

## 🛠️ Installation Requirements

### Graphviz (Required)
```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Windows (with Chocolatey)
choco install graphviz
```

### Python (Already installed)
Python 3.7+ with standard library (no additional packages needed)

## 🎯 Makefile Targets

```bash
make help            # Show all available targets
make all             # Generate all diagrams (default)
make architecture    # System architecture (enhanced + poster)
make dataflow        # Data flow diagram
make statemachine    # Gate state machine
make events          # Event publish/subscribe
make components      # Component architecture
make modules         # Module dependencies
make view            # Open diagram viewer
make clean           # Remove generated files
```

### Combined Commands
```bash
make clean all view  # Clean, regenerate everything, then view
make events modules  # Generate just event flow and module deps
```

## 📝 Direct Script Usage

If you prefer running the Python script directly:

```bash
./generate_diagrams.py              # Generate all
./generate_diagrams.py architecture # Specific diagram
./generate_diagrams.py events       # Another specific one
```

## 🖼️ Viewing Diagrams

### Option 1: Interactive Viewer (Recommended)
```bash
make view
# OR
./VIEW_DIAGRAMS.sh
```

Opens a beautiful web interface where you can:
- See all diagrams organized in cards
- Click to zoom any diagram
- View diagram descriptions and tags
- Professional gradient background

### Option 2: Direct File Access
```bash
cd diagrams/
xdg-open system_diagram_enhanced.png  # Linux
open system_diagram_enhanced.png      # macOS
start system_diagram_enhanced.png     # Windows
```

### Option 3: VS Code
Just click on any .png file in the diagrams/ directory

## 🎨 Customization

### Diagram Colors
Edit `COLORS` dictionary in `generate_diagrams.py`:

```python
COLORS = {
    'event_bus': '#667eea',    # Purple-blue
    'hardware': '#f56565',     # Red
    'tasks': '#48bb78',        # Green
    'util': '#ed8936',         # Orange
    # ... etc
}
```

### DPI Settings
Change resolution in `_run_dot()` calls:
```python
self._run_dot(dot, output_file, dpi=150)  # Screen
self._run_dot(dot, output_file, dpi=300)  # Print
```

## 🔧 Troubleshooting

### "Graphviz not found"
Install Graphviz (see Installation Requirements above)

### "Source directory not found"
Script expects this structure:
```
DustCollectorSoftware/
├── analysis/          # This directory
│   └── generate_diagrams.py
└── src/               # Your source code
    ├── hardware/
    ├── tasks/
    └── util/
```

### Empty diagrams
The generator uses AST parsing to find events and modules. If you're using unconventional patterns, you may need to adjust the regex patterns in `_analyze_events()`.

### Images not loading in viewer
Make sure:
1. You've run `make` to generate the PNGs
2. The diagrams/ directory exists
3. All PNG files are in diagrams/ subdirectory

## 📚 How It Works

### Code Analysis
1. **AST Parsing:** Analyzes all Python files in `src/` using Python's `ast` module
2. **Import Extraction:** Finds all import statements to build dependency graph
3. **Event Detection:** Uses regex to find `event_bus.publish()` and `subscribe()` calls
4. **Module Classification:** Groups modules by directory (hardware/tasks/util)

### Diagram Generation
1. **Graphviz DOT:** Creates DOT language specifications
2. **Rendering:** Executes `dot` command to generate PNG
3. **Multi-Resolution:** Creates both screen (150 DPI) and print (300 DPI) versions

## 🎓 Example Workflow

### Initial Setup
```bash
cd ~/DustCollectorSoftware/analysis
make
make view
```

### After Code Changes
```bash
make events          # Regenerate event flow
make view            # Check the changes
```

### Before Committing
```bash
make clean all       # Fresh regeneration
git add diagrams/    # Commit updated diagrams
```

### Documentation Update
```bash
make architecture    # Regenerate main diagram
# Copy system_diagram_poster.png to docs/
```

## 🚢 Sharing Diagrams

### For Documentation
Use the **poster version** (300 DPI) for:
- README.md files
- Wiki pages
- Design documents
- Presentations

### For Quick Reference
Use the **enhanced version** (150 DPI) for:
- Code reviews
- Slack/Teams messages
- Quick sharing
- Web pages

### For Interactive Viewing
Share the entire `analysis/` directory and tell people to run:
```bash
./VIEW_DIAGRAMS.sh
```

## 📄 License

Same license as the main Dust Collector project (your project, your rules!)

## 🙏 Credits

Generated with AI assistance using:
- Python AST module for code parsing
- Graphviz for diagram rendering
- Love and attention to detail ❤️

---

**Questions?** Just ask! This toolkit is designed to grow with your project.
