#!/usr/bin/env python3
"""
Analyze event flow in the dust collector codebase.
Extracts who publishes and who subscribes to what events.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class EventInfo:
    """Information about an event type."""
    publishers: Set[str] = field(default_factory=set)
    subscribers: Set[str] = field(default_factory=set)


@dataclass
class ModuleInfo:
    """Information about a module."""
    name: str
    publishes: Set[str] = field(default_factory=set)
    subscribes: Set[str] = field(default_factory=set)
    imports: Set[str] = field(default_factory=set)


class EventAnalyzer(ast.NodeVisitor):
    """AST visitor to extract event publishing patterns."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.publishes: Set[str] = set()
        self.subscribes = False
        self.imports: Set[str] = set()
    
    def visit_Call(self, node):
        # Look for bus.publish(Event.now("event.type", ...))
        if (isinstance(node.func, ast.Attribute) and 
            node.func.attr == 'publish'):
            # Check if first arg is Event.now()
            if node.args and isinstance(node.args[0], ast.Call):
                event_call = node.args[0]
                if (isinstance(event_call.func, ast.Attribute) and
                    event_call.func.attr == 'now' and
                    event_call.args):
                    # First arg to Event.now is the event type
                    event_type_node = event_call.args[0]
                    if isinstance(event_type_node, ast.Constant):
                        self.publishes.add(event_type_node.value)
                    elif isinstance(event_type_node, ast.JoinedStr):
                        # f-string like f"{tool}.on"
                        parts = []
                        for value in event_type_node.values:
                            if isinstance(value, ast.Constant):
                                parts.append(value.value)
                            elif isinstance(value, ast.FormattedValue):
                                parts.append("{...}")
                        self.publishes.add("".join(parts))
        
        # Look for bus.subscribe()
        if (isinstance(node.func, ast.Attribute) and 
            node.func.attr == 'subscribe'):
            self.subscribes = True
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def analyze_file(filepath: Path, module_name: str) -> ModuleInfo:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        analyzer = EventAnalyzer(module_name)
        analyzer.visit(tree)
        
        return ModuleInfo(
            name=module_name,
            publishes=analyzer.publishes,
            subscribes=set(['*']) if analyzer.subscribes else set(),
            imports=analyzer.imports
        )
    except Exception as e:
        print(f"Warning: Could not analyze {filepath}: {e}")
        return ModuleInfo(name=module_name)


def analyze_codebase(src_path: Path) -> Dict[str, ModuleInfo]:
    """Analyze all Python files in the codebase."""
    modules = {}
    
    for root, dirs, files in os.walk(src_path):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                rel_path = filepath.relative_to(src_path.parent)
                
                # Convert path to module name
                parts = list(rel_path.parts)
                if parts[-1] == '__init__.py':
                    parts = parts[:-1]
                else:
                    parts[-1] = parts[-1][:-3]  # Remove .py
                
                module_name = '.'.join(parts)
                modules[module_name] = analyze_file(filepath, module_name)
    
    return modules


def generate_event_flow_dot(modules: Dict[str, ModuleInfo]) -> str:
    """Generate a Graphviz DOT file showing event flow."""
    
    # Collect all events
    events: Dict[str, EventInfo] = {}
    for module in modules.values():
        for event_type in module.publishes:
            if event_type not in events:
                events[event_type] = EventInfo()
            events[event_type].publishers.add(module.name)
        
        if module.subscribes:
            # Module subscribes to all events it doesn't publish
            for event_type in events:
                if module.name not in events[event_type].publishers:
                    events[event_type].subscribers.add(module.name)
    
    lines = [
        'digraph EventFlow {',
        '  rankdir=LR;',
        '  node [shape=box, style=rounded];',
        '  ',
        '  // Event nodes',
    ]
    
    for event_type in sorted(events.keys()):
        safe_name = event_type.replace('.', '_').replace('{', '').replace('}', '').replace(' ', '')
        lines.append(f'  evt_{safe_name} [label="{event_type}", shape=ellipse, fillcolor=lightyellow, style=filled];')
    
    lines.append('  ')
    lines.append('  // Publishers')
    
    for event_type, info in sorted(events.items()):
        safe_event = event_type.replace('.', '_').replace('{', '').replace('}', '').replace(' ', '')
        for pub in sorted(info.publishers):
            safe_pub = pub.replace('.', '_')
            lines.append(f'  {safe_pub} [fillcolor=lightblue, style=filled];')
            lines.append(f'  {safe_pub} -> evt_{safe_event} [color=blue];')
    
    lines.append('  ')
    lines.append('  // Subscribers')
    
    for event_type, info in sorted(events.items()):
        safe_event = event_type.replace('.', '_').replace('{', '').replace('}', '').replace(' ', '')
        for sub in sorted(info.subscribers):
            if sub == '*':
                continue
            safe_sub = sub.replace('.', '_')
            lines.append(f'  {safe_sub} [fillcolor=lightgreen, style=filled];')
            lines.append(f'  evt_{safe_event} -> {safe_sub} [color=green];')
    
    lines.append('}')
    return '\n'.join(lines)


def generate_component_diagram(modules: Dict[str, ModuleInfo]) -> str:
    """Generate a component architecture diagram."""
    
    lines = [
        'digraph ComponentArchitecture {',
        '  rankdir=TB;',
        '  node [shape=component, style=filled];',
        '  compound=true;',
        '  ',
        '  subgraph cluster_hardware {',
        '    label="Hardware Layer";',
        '    style=filled;',
        '    fillcolor=lightgrey;',
    ]
    
    hw_modules = [m for m in modules.keys() if m.startswith('src.hardware')]
    for mod in sorted(hw_modules):
        safe_name = mod.replace('.', '_')
        display_name = mod.split('.')[-1]
        lines.append(f'    {safe_name} [label="{display_name}", fillcolor=lightblue];')
    
    lines.append('  }')
    lines.append('  ')
    lines.append('  subgraph cluster_tasks {')
    lines.append('    label="Task Layer";')
    lines.append('    style=filled;')
    lines.append('    fillcolor=lightyellow;')
    
    task_modules = [m for m in modules.keys() if m.startswith('src.tasks')]
    for mod in sorted(task_modules):
        safe_name = mod.replace('.', '_')
        display_name = mod.split('.')[-1]
        lines.append(f'    {safe_name} [label="{display_name}", fillcolor=lightgreen];')
    
    lines.append('  }')
    lines.append('  ')
    lines.append('  // Core components')
    
    core_modules = [m for m in modules.keys() 
                   if not m.startswith('src.hardware') 
                   and not m.startswith('src.tasks')
                   and not m.startswith('src.util')
                   and m != 'src']
    
    for mod in sorted(core_modules):
        safe_name = mod.replace('.', '_')
        display_name = mod.split('.')[-1]
        lines.append(f'  {safe_name} [label="{display_name}", fillcolor=orange, shape=box];')
    
    lines.append('  ')
    lines.append('  // Dependencies')
    
    for mod_name, mod_info in sorted(modules.items()):
        if mod_name.startswith('src.tasks'):
            safe_from = mod_name.replace('.', '_')
            for imp in mod_info.imports:
                if imp.startswith('..hardware'):
                    hw_mod = f'src.hardware.{imp.split(".")[-1]}'
                    if hw_mod in modules:
                        safe_to = hw_mod.replace('.', '_')
                        lines.append(f'  {safe_from} -> {safe_to} [style=dashed];')
    
    lines.append('}')
    return '\n'.join(lines)


def generate_module_deps(modules: Dict[str, ModuleInfo]) -> str:
    """Generate a module dependency graph."""
    
    lines = [
        'digraph ModuleDependencies {',
        '  rankdir=LR;',
        '  node [shape=box, style="rounded,filled"];',
        '  ',
    ]
    
    # Group by directory
    by_dir = {}
    for mod_name in modules:
        parts = mod_name.split('.')
        if len(parts) > 1:
            dir_name = '.'.join(parts[:-1])
            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append(mod_name)
    
    for dir_name, mods in sorted(by_dir.items()):
        cluster_name = dir_name.replace('.', '_')
        lines.append(f'  subgraph cluster_{cluster_name} {{')
        lines.append(f'    label="{dir_name}";')
        lines.append('    style=filled;')
        lines.append('    fillcolor=lightgrey;')
        
        for mod in sorted(mods):
            safe_name = mod.replace('.', '_')
            display_name = mod.split('.')[-1]
            lines.append(f'    {safe_name} [label="{display_name}", fillcolor=white];')
        
        lines.append('  }')
    
    lines.append('  ')
    lines.append('  // Dependencies')
    
    for mod_name, mod_info in sorted(modules.items()):
        safe_from = mod_name.replace('.', '_')
        for imp in mod_info.imports:
            # Try to resolve relative imports
            if imp.startswith('..'):
                parts = mod_name.split('.')[:-1]  # Remove current module
                imp_parts = imp.split('.')
                
                # Go up directories
                while imp_parts and imp_parts[0] == '':
                    imp_parts = imp_parts[1:]
                    if parts:
                        parts = parts[:-1]
                
                target = '.'.join(parts + imp_parts)
                if target in modules:
                    safe_to = target.replace('.', '_')
                    lines.append(f'  {safe_from} -> {safe_to};')
    
    lines.append('}')
    return '\n'.join(lines)


def main():
    src_path = Path(__file__).parent / 'src'
    
    print("Analyzing codebase...")
    modules = analyze_codebase(src_path)
    
    print(f"Found {len(modules)} modules")
    
    # Generate event flow diagram
    print("Generating event flow diagram...")
    event_dot = generate_event_flow_dot(modules)
    with open('event_flow.dot', 'w') as f:
        f.write(event_dot)
    print("  -> event_flow.dot")
    
    # Generate component diagram
    print("Generating component architecture diagram...")
    component_dot = generate_component_diagram(modules)
    with open('component_architecture.dot', 'w') as f:
        f.write(component_dot)
    print("  -> component_architecture.dot")
    
    # Generate module dependencies
    print("Generating module dependency diagram...")
    module_dot = generate_module_deps(modules)
    with open('module_dependencies.dot', 'w') as f:
        f.write(module_dot)
    print("  -> module_dependencies.dot")
    
    # Print summary
    print("\n=== Event Flow Summary ===")
    events = {}
    for module in modules.values():
        for event in module.publishes:
            if event not in events:
                events[event] = {'publishers': [], 'subscribers': []}
            events[event]['publishers'].append(module.name)
    
    for event_type in sorted(events.keys()):
        pubs = events[event_type]['publishers']
        print(f"\n{event_type}:")
        print(f"  Publishers: {', '.join(pubs)}")


if __name__ == '__main__':
    main()
