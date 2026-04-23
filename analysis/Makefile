# Dust Collector System Analysis Makefile
#
# Targets:
#   all           - Generate all diagrams (default)
#   architecture  - System architecture diagrams
#   dataflow      - Data flow diagram
#   statemachine  - Gate state machine diagram
#   events        - Event publish/subscribe diagram
#   components    - Component architecture diagram
#   modules       - Module dependency diagram
#   view          - Open diagram viewer in browser
#   clean         - Remove all generated diagrams
#   help          - Show this help

PYTHON := python3
GENERATOR := ./generate_diagrams.py
VIEWER := ./VIEW_DIAGRAMS.sh
DIAGRAM_DIR := diagrams

# Colors for output
GREEN := \033[0;32m
BLUE := \033[0;34m
RESET := \033[0m

.PHONY: all architecture dataflow statemachine events components modules view clean help

# Default target
all: architecture dataflow statemachine events components modules
	@echo "$(GREEN)✅ All diagrams generated!$(RESET)"
	@echo "   Run 'make view' to see them in your browser"

# Individual diagram targets
architecture:
	@echo "$(BLUE)📐 Generating system architecture...$(RESET)"
	@$(PYTHON) $(GENERATOR) architecture

dataflow:
	@echo "$(BLUE)📊 Generating data flow diagram...$(RESET)"
	@$(PYTHON) $(GENERATOR) dataflow

statemachine:
	@echo "$(BLUE)🔄 Generating state machine...$(RESET)"
	@$(PYTHON) $(GENERATOR) statemachine

events:
	@echo "$(BLUE)📡 Generating event flow...$(RESET)"
	@$(PYTHON) $(GENERATOR) events

components:
	@echo "$(BLUE)🏗️  Generating component architecture...$(RESET)"
	@$(PYTHON) $(GENERATOR) components

modules:
	@echo "$(BLUE)📦 Generating module dependencies...$(RESET)"
	@$(PYTHON) $(GENERATOR) modules

# View diagrams in browser
view:
	@if [ -f "$(VIEWER)" ]; then \
		echo "$(BLUE)🌐 Opening diagram viewer...$(RESET)"; \
		bash $(VIEWER); \
	else \
		echo "$(GREEN)Opening diagrams directory...$(RESET)"; \
		xdg-open $(DIAGRAM_DIR) 2>/dev/null || open $(DIAGRAM_DIR) 2>/dev/null || echo "Please open $(DIAGRAM_DIR) manually"; \
	fi

# Clean generated files
clean:
	@echo "$(BLUE)🧹 Cleaning generated diagrams...$(RESET)"
	@rm -f $(DIAGRAM_DIR)/*.png
	@rm -f $(DIAGRAM_DIR)/*.dot
	@echo "$(GREEN)✓ Clean complete$(RESET)"

# Help
help:
	@echo "Dust Collector System Analysis Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all           - Generate all diagrams (default)"
	@echo "  architecture  - System architecture diagrams (enhanced + poster)"
	@echo "  dataflow      - Data flow from sensors to actuators"
	@echo "  statemachine  - Gate control state machine"
	@echo "  events        - Event publish/subscribe relationships"
	@echo "  components    - Component architecture layers"
	@echo "  modules       - Module dependency graph"
	@echo "  view          - Open diagram viewer in browser"
	@echo "  clean         - Remove all generated diagrams"
	@echo "  help          - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make                    # Generate everything"
	@echo "  make architecture       # Just the main system diagram"
	@echo "  make events modules     # Multiple specific diagrams"
	@echo "  make clean all view     # Clean, regenerate, and view"
