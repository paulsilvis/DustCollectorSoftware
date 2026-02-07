# Dust Collector System Diagrams

Automated system visualization for the dust collector control system.

## Generated Diagrams

### 1. System Architecture (Enhanced) 
**File:** `system_diagram_enhanced.png`

The main architectural diagram showing:
- Event Bus (central pub/sub messaging)
- Hardware Abstraction Layer (I2C, UART, GPIO)
- Control Tasks (async event-driven controllers)
- Event types and flow
- Hardware connections

**Use:** Main diagram for explaining system architecture to visitors

### 2. Data Flow Diagram
**File:** `dataflow_diagram.png`

Shows the complete data flow from physical sensors to physical outputs:
- Current sensors → ADC → Signal processing → Events → Controllers → Gates/Fan/LEDs
- Hysteresis filtering and debouncing
- Real-time event propagation

**Use:** Explain how tool detection triggers the system

### 3. State Machine
**File:** `state_machine.png`

Blast gate controller state machine:
- States: CLOSED, OPENING, OPEN, CLOSING
- Transitions on tool.on/tool.off events
- Timer-based transitions
- Cancel logic

**Use:** Detail view of gate control logic

### 4. Event Flow
**File:** `event_flow.png`

Event publish/subscribe relationships:
- Blue nodes: Event publishers
- Yellow nodes: Events
- Green nodes: Event subscribers
- Shows message flow through the system

**Use:** Debug event routing, understand message patterns

### 5. Component Architecture
**File:** `component_architecture.png`

Layered architecture view:
- Hardware Layer (grouped by subsystem)
- Task Layer (controllers and sensors)
- Dependencies between layers

**Use:** High-level architectural overview

### 6. Module Dependencies
**File:** `module_dependencies.png`

Python module import graph:
- Shows which modules depend on which
- Grouped by package
- Useful for code maintenance

**Use:** Code structure and dependency analysis

## Regenerating Diagrams

### Prerequisites
```bash
# Install Graphviz
sudo apt-get install graphviz

# Python 3 (already installed)
```

### Generate All Diagrams
```bash
# Analyze codebase and generate base diagrams
python3 analyze_events.py

# Generate enhanced visual diagrams
python3 generate_enhanced_diagrams.py

# Convert DOT files to PNG
./generate_all_pngs.sh

# Or convert to SVG (better for zooming)
./generate_all_svgs.sh
```

### Manual Generation
```bash
# Individual diagrams
dot -Tpng system_diagram_enhanced.dot -o system_diagram_enhanced.png
dot -Tsvg system_diagram_enhanced.dot -o system_diagram_enhanced.svg

# High resolution
dot -Tpng -Gdpi=300 system_diagram_enhanced.dot -o system_diagram_enhanced_hires.png
```

## Customization

### Edit Diagram Styles
Edit the generator scripts to customize:
- `generate_enhanced_diagrams.py` - Visual style, colors, layout
- `analyze_events.py` - Auto-generated diagrams from code analysis

### Change Colors
In the DOT files, colors use:
- Hex colors: `#FF6B6B`
- Gradients: `fillcolor="#FF6B6B:#C92A2A"`
- Named colors: `lightblue`, `green`, etc.

### Layout Options
Change `rankdir` in DOT files:
- `TB` - Top to Bottom (default for most)
- `LR` - Left to Right (used for flow diagrams)
- `BT` - Bottom to Top
- `RL` - Right to Left

## Integration Ideas

### For Shop Display
1. Print large format posters (system_diagram_enhanced works best)
2. Display on a monitor/tablet in the shop
3. Include in documentation binder
4. Add QR code linking to live system status

### For Documentation
1. Include in README.md
2. Add to wiki/docs site
3. Generate PDF with all diagrams
4. Create animated SVGs showing event flow

### Code Annotations
To enhance auto-generation, you can add structured comments:

```python
# @publishes: tool.on, tool.off
# @subscribes: *
# @hardware: ADS1115 @ I2C 0x48
```

Then extend `analyze_events.py` to parse these annotations.

## Diagram Tools Used

- **Graphviz DOT** - Graph description language
- **Python AST** - Code analysis for event extraction
- **dot** - Layout engine (part of Graphviz)

## Tips

1. **SVG vs PNG**: Use SVG for web/screen display (infinite zoom), PNG for print
2. **High DPI**: Add `-Gdpi=300` for print-quality output
3. **Large Graphs**: Use `dot -Tpng:cairo` for better rendering of large graphs
4. **Interactive**: Try `dot -Tsvg` and add JavaScript for interactive diagrams

## Future Enhancements

- [ ] Add runtime metrics overlay (which events are most frequent)
- [ ] Animated SVG showing event propagation
- [ ] Web dashboard with live event visualization
- [ ] Sequence diagrams for specific scenarios
- [ ] Timing diagrams showing relay sequences
- [ ] 3D visualization of physical layout
