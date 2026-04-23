#!/bin/bash
# Generate all diagrams as SVG files (better for web display and zooming)

set -e

echo "Generating SVG diagrams..."

# Base diagrams
dot -Tsvg event_flow.dot -o event_flow.svg
dot -Tsvg component_architecture.dot -o component_architecture.svg
dot -Tsvg module_dependencies.dot -o module_dependencies.svg

# Enhanced diagrams
dot -Tsvg system_diagram_enhanced.dot -o system_diagram_enhanced.svg
dot -Tsvg dataflow_diagram.dot -o dataflow_diagram.svg
dot -Tsvg state_machine.dot -o state_machine.svg

echo "Done! Generated SVG files:"
ls -lh *.svg

echo ""
echo "SVG files are ideal for:"
echo "  - Web display (infinite zoom without quality loss)"
echo "  - Documentation websites"
echo "  - Interactive diagrams (can add JavaScript)"
