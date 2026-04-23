#!/usr/bin/env python3
"""
Dust Collector System Analysis and Diagram Generator

Analyzes the event-driven dust collector codebase and generates
comprehensive architecture diagrams using Graphviz.

Usage:
    ./generate_diagrams.py [diagram_type]
    
    diagram_type can be: all, architecture, dataflow, statemachine, 
                        events, components, modules
"""

import os
import sys
import ast
import re
from pathlib import Path
from collections import defaultdict
import subprocess

# Color scheme for diagrams
COLORS = {
    'event_bus': '#667eea',
    'hardware': '#f56565',
    'tasks': '#48bb78',
    'util': '#ed8936',
    'tool': '#9f7aea',
    'gate': '#38b2ac',
    'fan': '#4299e1',
    'sensor': '#f6ad55',
    'background': '#ffffff',
    'text': '#2d3748',
    'border': '#cbd5e0'
}


class CodeAnalyzer:
    """Analyzes Python source code to extract architecture information"""
    
    def __init__(self, src_dir):
        self.src_dir = Path(src_dir)
        self.modules = {}
        self.imports = defaultdict(set)
        self.classes = defaultdict(list)
        self.events = defaultdict(set)  # module -> set of events
        self.event_publishers = defaultdict(set)  # event -> set of publishers
        self.event_subscribers = defaultdict(set)  # event -> set of subscribers
        
    def analyze(self):
        """Run complete analysis"""
        print("🔍 Analyzing codebase...")
        self._scan_modules()
        self._analyze_imports()
        self._analyze_events()
        print(f"   Found {len(self.modules)} modules")
        print(f"   Found {len(self.classes)} classes")
        print(f"   Found {len(self.event_publishers)} event types")
        
    def _scan_modules(self):
        """Find and parse all Python modules"""
        for py_file in self.src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            module_path = py_file.relative_to(self.src_dir)
            module_name = str(module_path).replace('/', '.').replace('.py', '')
            
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                    self.modules[module_name] = {
                        'path': py_file,
                        'tree': tree,
                        'classes': [node.name for node in ast.walk(tree) 
                                   if isinstance(node, ast.ClassDef)]
                    }
            except Exception as e:
                print(f"   Warning: Could not parse {module_name}: {e}")
    
    def _analyze_imports(self):
        """Extract import relationships"""
        for module_name, module_info in self.modules.items():
            tree = module_info['tree']
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports[module_name].add(node.module)
    
    def _analyze_events(self):
        """Extract event publish/subscribe patterns"""
        for module_name, module_info in self.modules.items():
            tree = module_info['tree']
            source = ast.unparse(tree)
            
            # Find publish calls
            publish_pattern = r'(?:event_bus|self\.event_bus|bus)\.publish\(["\'](\w+)["\']'
            for match in re.finditer(publish_pattern, source):
                event_name = match.group(1)
                self.event_publishers[event_name].add(module_name)
                self.events[module_name].add(event_name)
            
            # Find subscribe calls
            subscribe_pattern = r'(?:event_bus|self\.event_bus|bus)\.subscribe\(["\'](\w+)["\']'
            for match in re.finditer(subscribe_pattern, source):
                event_name = match.group(1)
                self.event_subscribers[event_name].add(module_name)
                self.events[module_name].add(event_name)


class DiagramGenerator:
    """Generates Graphviz diagrams from analyzed code"""
    
    def __init__(self, analyzer, output_dir):
        self.analyzer = analyzer
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _run_dot(self, dot_content, output_file, dpi=150):
        """Execute Graphviz dot command"""
        dot_file = self.output_dir / f"{output_file.stem}.dot"
        
        # Write DOT file
        with open(dot_file, 'w') as f:
            f.write(dot_content)
        
        # Generate PNG
        cmd = ['dot', '-Tpng', f'-Gdpi={dpi}', '-o', str(output_file), str(dot_file)]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"   ✓ Generated {output_file.name}")
            # Clean up DOT file
            dot_file.unlink()
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Error generating {output_file.name}: {e.stderr.decode()}")
        except FileNotFoundError:
            print("   ✗ Error: Graphviz not found. Install with: sudo apt-get install graphviz")
            sys.exit(1)
    
    def generate_architecture(self):
        """Generate system architecture diagram"""
        print("📐 Generating system architecture diagram...")
        
        dot = f'''digraph system_architecture {{
    rankdir=TB;
    bgcolor="{COLORS['background']}";
    node [shape=box, style="rounded,filled", fontname="Arial"];
    edge [fontname="Arial", fontsize=10];
    
    // Event Bus (central)
    subgraph cluster_event_bus {{
        label="Event Bus";
        style=filled;
        color="{COLORS['event_bus']}";
        fillcolor="{COLORS['event_bus']}20";
        
        event_bus [label="Event Bus\\n(Pub/Sub)", fillcolor="{COLORS['event_bus']}", fontcolor=white];
    }}
    
    // Hardware Layer
    subgraph cluster_hardware {{
        label="Hardware Abstraction Layer";
        style=filled;
        color="{COLORS['hardware']}";
        fillcolor="{COLORS['hardware']}20";
        
        tools [label="Tool Detection\\n(Current Sensors)", fillcolor="{COLORS['sensor']}"];
        gates [label="Blast Gates\\n(Servo Control)", fillcolor="{COLORS['gate']}"];
        fans [label="Fan Control\\n(Relay)", fillcolor="{COLORS['fan']}"];
        air_quality [label="Air Quality\\n(UART Sensor)", fillcolor="{COLORS['sensor']}"];
        io_expander [label="I/O Expander\\n(PCF8574)", fillcolor="{COLORS['hardware']}"];
    }}
    
    // Control Tasks
    subgraph cluster_tasks {{
        label="Control Tasks";
        style=filled;
        color="{COLORS['tasks']}";
        fillcolor="{COLORS['tasks']}20";
        
        tool_monitor [label="Tool Monitor", fillcolor="{COLORS['tasks']}"];
        gate_control [label="Gate Controller", fillcolor="{COLORS['tasks']}"];
        fan_control [label="Fan Controller", fillcolor="{COLORS['tasks']}"];
        air_monitor [label="Air Quality Monitor", fillcolor="{COLORS['tasks']}"];
    }}
    
    // Event flow
    tool_monitor -> event_bus [label="tool_on\\ntool_off"];
    event_bus -> gate_control [label="subscribe"];
    event_bus -> fan_control [label="subscribe"];
    gate_control -> event_bus [label="gate_opened\\ngate_closed"];
    fan_control -> event_bus [label="fan_on\\nfan_off"];
    air_monitor -> event_bus [label="air_quality"];
    
    // Hardware connections
    tool_monitor -> tools [style=dashed, label="read"];
    gate_control -> gates [style=dashed, label="control"];
    fan_control -> fans [style=dashed, label="control"];
    air_monitor -> air_quality [style=dashed, label="read"];
    
    // I2C bus
    {{tools, gates, io_expander}} -> i2c_bus [style=dotted, label="I²C"];
    i2c_bus [label="I²C Bus", shape=cylinder, fillcolor="{COLORS['border']}"];
}}'''
        
        self._run_dot(dot, self.output_dir / 'system_diagram_enhanced.png', dpi=150)
        self._run_dot(dot, self.output_dir / 'system_diagram_poster.png', dpi=300)
    
    def generate_dataflow(self):
        """Generate data flow diagram"""
        print("📊 Generating data flow diagram...")
        
        dot = f'''digraph dataflow {{
    rankdir=LR;
    bgcolor="{COLORS['background']}";
    node [shape=box, style="rounded,filled", fontname="Arial"];
    edge [fontname="Arial"];
    
    // Sensors
    current_sensor [label="Current Sensor\\n(ADS1115)", fillcolor="{COLORS['sensor']}"];
    air_sensor [label="Air Quality\\nSensor", fillcolor="{COLORS['sensor']}"];
    
    // Processing
    adc_read [label="ADC Reading\\n(I²C)", fillcolor="{COLORS['util']}"];
    threshold [label="Threshold\\nDetection", fillcolor="{COLORS['util']}"];
    debounce [label="Debouncing\\n(100ms)", fillcolor="{COLORS['util']}"];
    
    // Events
    events [label="Event\\nPublication", shape=ellipse, fillcolor="{COLORS['event_bus']}"];
    
    // Control
    gate_logic [label="Gate State\\nMachine", fillcolor="{COLORS['tasks']}"];
    fan_logic [label="Fan Control\\nLogic", fillcolor="{COLORS['tasks']}"];
    
    // Actuators
    servo [label="Servo\\nControl", fillcolor="{COLORS['gate']}"];
    relay [label="Relay\\nControl", fillcolor="{COLORS['fan']}"];
    
    // Flow
    current_sensor -> adc_read -> threshold -> debounce -> events;
    air_sensor -> events;
    events -> gate_logic -> servo;
    events -> fan_logic -> relay;
    
    // Labels
    adc_read -> threshold [label="mA"];
    threshold -> debounce [label="bool"];
    debounce -> events [label="tool_on/off"];
    events -> gate_logic [label="subscribe"];
    events -> fan_logic [label="subscribe"];
}}'''
        
        self._run_dot(dot, self.output_dir / 'dataflow_diagram.png')
    
    def generate_state_machine(self):
        """Generate gate control state machine"""
        print("🔄 Generating state machine diagram...")
        
        dot = f'''digraph state_machine {{
    rankdir=LR;
    bgcolor="{COLORS['background']}";
    node [shape=circle, style=filled, fontname="Arial"];
    edge [fontname="Arial"];
    
    // States
    start [shape=doublecircle, fillcolor="{COLORS['border']}"];
    closed [label="CLOSED", fillcolor="{COLORS['gate']}"];
    opening [label="OPENING", fillcolor="{COLORS['util']}"];
    open [label="OPEN", fillcolor="{COLORS['tasks']}"];
    closing [label="CLOSING", fillcolor="{COLORS['util']}"];
    
    // Transitions
    start -> closed;
    closed -> opening [label="tool_on"];
    opening -> open [label="servo_done"];
    open -> closing [label="tool_off"];
    closing -> closed [label="servo_done"];
    
    // Self loops
    closed -> closed [label="tool_off"];
    open -> open [label="tool_on"];
}}'''
        
        self._run_dot(dot, self.output_dir / 'state_machine.png')
    
    def generate_event_flow(self):
        """Generate event publish/subscribe diagram"""
        print("📡 Generating event flow diagram...")
        
        if not self.analyzer.event_publishers:
            print("   ⚠ No events found in code - generating example diagram")
            events = {
                'tool_on': (['tool_monitor'], ['gate_control', 'fan_control']),
                'tool_off': (['tool_monitor'], ['gate_control', 'fan_control']),
                'gate_opened': (['gate_control'], ['fan_control']),
                'gate_closed': (['gate_control'], ['fan_control']),
                'fan_on': (['fan_control'], []),
                'air_quality': (['air_monitor'], [])
            }
        else:
            events = {
                event: (list(self.analyzer.event_publishers[event]),
                       list(self.analyzer.event_subscribers[event]))
                for event in self.analyzer.event_publishers.keys()
            }
        
        dot_lines = [
            'digraph event_flow {',
            '    rankdir=LR;',
            f'    bgcolor="{COLORS["background"]}";',
            '    node [shape=box, style="rounded,filled", fontname="Arial"];',
            '    edge [fontname="Arial"];',
            ''
        ]
        
        # Create nodes for publishers and subscribers
        publishers = set()
        subscribers = set()
        for pubs, subs in events.values():
            publishers.update(pubs)
            subscribers.update(subs)
        
        # Publisher nodes
        dot_lines.append('    subgraph cluster_publishers {')
        dot_lines.append('        label="Publishers";')
        dot_lines.append(f'        fillcolor="{COLORS["event_bus"]}20";')
        dot_lines.append('        style=filled;')
        for pub in sorted(publishers):
            name = pub.split('.')[-1]
            dot_lines.append(f'        pub_{name} [label="{name}", fillcolor="{COLORS["event_bus"]}"];')
        dot_lines.append('    }')
        dot_lines.append('')
        
        # Event nodes
        dot_lines.append('    subgraph cluster_events {')
        dot_lines.append('        label="Events";')
        dot_lines.append(f'        fillcolor="{COLORS["util"]}20";')
        dot_lines.append('        style=filled;')
        for event in sorted(events.keys()):
            dot_lines.append(f'        evt_{event} [label="{event}", shape=ellipse, fillcolor="{COLORS["util"]}"];')
        dot_lines.append('    }')
        dot_lines.append('')
        
        # Subscriber nodes
        if subscribers:
            dot_lines.append('    subgraph cluster_subscribers {')
            dot_lines.append('        label="Subscribers";')
            dot_lines.append(f'        fillcolor="{COLORS["tasks"]}20";')
            dot_lines.append('        style=filled;')
            for sub in sorted(subscribers):
                name = sub.split('.')[-1]
                dot_lines.append(f'        sub_{name} [label="{name}", fillcolor="{COLORS["tasks"]}"];')
            dot_lines.append('    }')
            dot_lines.append('')
        
        # Connections
        for event, (pubs, subs) in events.items():
            for pub in pubs:
                pub_name = pub.split('.')[-1]
                dot_lines.append(f'    pub_{pub_name} -> evt_{event} [label="publish"];')
            for sub in subs:
                sub_name = sub.split('.')[-1]
                dot_lines.append(f'    evt_{event} -> sub_{sub_name} [label="subscribe"];')
        
        dot_lines.append('}')
        
        self._run_dot('\n'.join(dot_lines), self.output_dir / 'event_flow.png')
    
    def generate_components(self):
        """Generate component architecture diagram"""
        print("🏗️  Generating component architecture...")
        
        # Collect all modules and group by layer
        hardware_modules = []
        tasks_modules = []
        util_modules = []
        root_modules = []
        
        for module_name in self.analyzer.modules.keys():
            # Get the simple name for display
            simple_name = module_name.split('.')[-1]
            if simple_name == '__init__':
                continue  # Skip __init__ files
                
            if 'hardware' in module_name:
                hardware_modules.append(simple_name)
            elif 'tasks' in module_name:
                tasks_modules.append(simple_name)
            elif 'util' in module_name:
                util_modules.append(simple_name)
            else:
                root_modules.append(simple_name)
        
        print(f"   Hardware: {len(hardware_modules)} modules")
        print(f"   Tasks: {len(tasks_modules)} modules")
        print(f"   Util: {len(util_modules)} modules")
        print(f"   Root: {len(root_modules)} modules")
        
        dot_lines = [
            'digraph components {',
            '    rankdir=TB;',
            f'    bgcolor="{COLORS["background"]}";',
            '    node [shape=box, style="rounded,filled", fontname="Arial", margin=0.2];',
            '    edge [fontname="Arial", color="#888"];',
            '    ranksep=1.0;',
            '    nodesep=0.5;',
            ''
        ]
        
        # Util layer (top)
        if util_modules:
            dot_lines.append('    subgraph cluster_util {')
            dot_lines.append('        label="Utility Layer";')
            dot_lines.append(f'        fillcolor="{COLORS["util"]}20";')
            dot_lines.append('        style="filled,rounded";')
            dot_lines.append('        rank=same;')
            for mod in sorted(util_modules):
                dot_lines.append(f'        util_{mod} [label="{mod}", fillcolor="{COLORS["util"]}"];')
            dot_lines.append('    }')
            dot_lines.append('')
        
        # Hardware layer (middle)
        if hardware_modules:
            dot_lines.append('    subgraph cluster_hardware {')
            dot_lines.append('        label="Hardware Abstraction Layer";')
            dot_lines.append(f'        fillcolor="{COLORS["hardware"]}20";')
            dot_lines.append('        style="filled,rounded";')
            dot_lines.append('        rank=same;')
            for mod in sorted(hardware_modules):
                dot_lines.append(f'        hw_{mod} [label="{mod}", fillcolor="{COLORS["hardware"]}"];')
            dot_lines.append('    }')
            dot_lines.append('')
        
        # Tasks layer (bottom)
        if tasks_modules:
            dot_lines.append('    subgraph cluster_tasks {')
            dot_lines.append('        label="Control Tasks Layer";')
            dot_lines.append(f'        fillcolor="{COLORS["tasks"]}20";')
            dot_lines.append('        style="filled,rounded";')
            dot_lines.append('        rank=same;')
            for mod in sorted(tasks_modules):
                dot_lines.append(f'        task_{mod} [label="{mod}", fillcolor="{COLORS["tasks"]}"];')
            dot_lines.append('    }')
            dot_lines.append('')
        
        # Root modules if any
        if root_modules:
            for mod in sorted(root_modules):
                dot_lines.append(f'    root_{mod} [label="{mod}", fillcolor="{COLORS["border"]}"];')
            dot_lines.append('')
        
        # Add some example layer relationships
        if util_modules and hardware_modules:
            util_first = sorted(util_modules)[0]
            hw_first = sorted(hardware_modules)[0]
            dot_lines.append(f'    util_{util_first} -> hw_{hw_first} [style=invis];')
        
        if hardware_modules and tasks_modules:
            hw_first = sorted(hardware_modules)[0]
            task_first = sorted(tasks_modules)[0]
            dot_lines.append(f'    hw_{hw_first} -> task_{task_first} [style=invis];')
        
        dot_lines.append('}')
        
        self._run_dot('\n'.join(dot_lines), self.output_dir / 'component_architecture.png')
    
    def generate_modules(self):
        """Generate module dependency graph"""
        print("📦 Generating module dependencies...")
        
        # Build a mapping of simple names to full names
        name_to_module = {}
        module_to_simple = {}
        
        for full_module in self.analyzer.modules.keys():
            simple = full_module.split('.')[-1]
            if simple == '__init__':
                # Use parent directory name for __init__ files
                simple = full_module.split('.')[-2] if len(full_module.split('.')) > 1 else 'init'
            
            # Handle duplicates by prefixing with parent
            if simple in name_to_module:
                # Make unique by adding parent
                parts = full_module.split('.')
                if len(parts) >= 2:
                    simple = f"{parts[-2]}_{simple}"
            
            name_to_module[simple] = full_module
            module_to_simple[full_module] = simple
        
        print(f"   Processing {len(name_to_module)} unique modules")
        
        # Group for coloring
        def get_group(module_name):
            if 'hardware' in module_name:
                return 'hardware'
            elif 'tasks' in module_name:
                return 'tasks'
            elif 'util' in module_name:
                return 'util'
            else:
                return 'root'
        
        groups = defaultdict(list)
        for full_module, simple in module_to_simple.items():
            group = get_group(full_module)
            groups[group].append((simple, full_module))
        
        dot_lines = [
            'digraph modules {',
            '    rankdir=LR;',
            f'    bgcolor="{COLORS["background"]}";',
            '    node [shape=box, style="rounded,filled", fontname="Arial"];',
            '    edge [fontname="Arial", color="#666"];',
            ''
        ]
        
        # Create subgraphs for each group
        for group_name in ['util', 'hardware', 'tasks', 'root']:
            if group_name not in groups or not groups[group_name]:
                continue
                
            color = COLORS.get(group_name, COLORS['border'])
            dot_lines.append(f'    subgraph cluster_{group_name} {{')
            dot_lines.append(f'        label="{group_name}";')
            dot_lines.append(f'        fillcolor="{color}20";')
            dot_lines.append('        style="filled,rounded";')
            
            for simple, full_module in sorted(groups[group_name]):
                safe_name = simple.replace('-', '_')
                dot_lines.append(f'        {safe_name} [label="{simple}", fillcolor="{color}"];')
            
            dot_lines.append('    }')
            dot_lines.append('')
        
        # Add import relationships
        edges_added = 0
        for source_full, imports in self.analyzer.imports.items():
            if source_full not in module_to_simple:
                continue
            
            source_simple = module_to_simple[source_full].replace('-', '_')
            
            for imp in imports:
                # Only show imports to our own modules
                if imp in module_to_simple:
                    target_simple = module_to_simple[imp].replace('-', '_')
                    if source_simple != target_simple:  # No self-loops
                        dot_lines.append(f'    {source_simple} -> {target_simple};')
                        edges_added += 1
        
        print(f"   Found {edges_added} import relationships")
        
        dot_lines.append('}')
        
        self._run_dot('\n'.join(dot_lines), self.output_dir / 'module_dependencies.png')


def main():
    """Main entry point"""
    # Determine what to generate
    if len(sys.argv) > 1:
        diagram_type = sys.argv[1].lower()
    else:
        diagram_type = 'all'
    
    # Find source directory
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent if script_dir.name == 'analysis' else script_dir
    src_dir = project_root / 'src'
    
    if not src_dir.exists():
        print(f"❌ Error: Source directory not found: {src_dir}")
        print(f"   Script location: {Path(__file__)}")
        print(f"   Detected project root: {project_root}")
        print()
        print("Expected project structure:")
        print("   DustCollectorSoftware/")
        print("   ├── analysis/          (you are here)")
        print("   │   └── generate_diagrams.py")
        print("   └── src/               (not found!)")
        print("       ├── hardware/")
        print("       ├── tasks/")
        print("       └── util/")
        print()
        print("Actual structure found:")
        if project_root.exists():
            print(f"   {project_root}/")
            for item in sorted(project_root.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    print(f"   ├── {item.name}/")
        sys.exit(1)
    
    # Output directory
    output_dir = script_dir / 'diagrams' if script_dir.name == 'analysis' else script_dir / 'dust_collector_diagrams'
    
    print(f"🎯 Dust Collector System Analysis")
    print(f"   Script: {Path(__file__)}")
    print(f"   Script dir: {script_dir}")
    print(f"   Project root: {project_root}")
    print(f"   Source: {src_dir}")
    print(f"   Output: {output_dir}")
    print()
    
    # Analyze code
    analyzer = CodeAnalyzer(src_dir)
    analyzer.analyze()
    print()
    
    # Generate diagrams
    generator = DiagramGenerator(analyzer, output_dir)
    
    generators = {
        'architecture': generator.generate_architecture,
        'dataflow': generator.generate_dataflow,
        'statemachine': generator.generate_state_machine,
        'events': generator.generate_event_flow,
        'components': generator.generate_components,
        'modules': generator.generate_modules
    }
    
    if diagram_type == 'all':
        for gen_func in generators.values():
            gen_func()
    elif diagram_type in generators:
        generators[diagram_type]()
    else:
        print(f"❌ Unknown diagram type: {diagram_type}")
        print(f"   Valid types: all, {', '.join(generators.keys())}")
        sys.exit(1)
    
    print()
    print(f"✅ Done! Diagrams saved to: {output_dir}")
    print(f"   View them by running: ./VIEW_DIAGRAMS.sh")


if __name__ == '__main__':
    main()
