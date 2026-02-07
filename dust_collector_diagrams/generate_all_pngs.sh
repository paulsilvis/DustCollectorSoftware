#!/bin/bash
# Generate all diagrams as PNG files

set -e

echo "Generating PNG diagrams..."

# Base diagrams
dot -Tpng event_flow.dot -o event_flow.png
dot -Tpng component_architecture.dot -o component_architecture.png
dot -Tpng module_dependencies.dot -o module_dependencies.png

# Enhanced diagrams
dot -Tpng system_diagram_enhanced.dot -o system_diagram_enhanced.png
dot -Tpng dataflow_diagram.dot -o dataflow_diagram.png
dot -Tpng state_machine.dot -o state_machine.png

echo "Done! Generated PNG files:"
ls -lh *.png

echo ""
echo "For high-resolution output (300 DPI):"
echo "  dot -Tpng -Gdpi=300 <file>.dot -o <file>_hires.png"
