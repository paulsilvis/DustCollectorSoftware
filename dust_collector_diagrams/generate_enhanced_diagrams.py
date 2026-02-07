#!/usr/bin/env python3
"""
Generate enhanced, visually appealing system diagrams for shop display.
"""

from pathlib import Path


def generate_enhanced_system_diagram() -> str:
    """Generate a comprehensive system diagram with great visual style."""
    
    return '''digraph DustCollectorSystem {
  // Overall graph settings
  rankdir=TB;
  compound=true;
  bgcolor="#f8f8f8";
  fontname="Arial";
  fontsize=14;
  
  node [fontname="Arial", fontsize=11, style=filled];
  edge [fontname="Arial", fontsize=9];
  
  // Title
  labelloc=t;
  label=<<B><FONT POINT-SIZE="18">Dust Collector Control System</FONT></B><BR/><FONT POINT-SIZE="12">Event-Driven Architecture</FONT>>;
  
  // Event Bus - Central component
  event_bus [
    label=<<B>Event Bus</B><BR/><FONT POINT-SIZE="9">Pub/Sub Message Broker</FONT>>,
    shape=cylinder,
    fillcolor="#FF6B6B:#C92A2A",
    gradientangle=270,
    fontcolor=white,
    penwidth=2
  ];
  
  // Hardware Layer
  subgraph cluster_hardware {
    label=<<B>Hardware Abstraction Layer</B>>;
    style=filled;
    fillcolor="#E3F2FD";
    color="#1976D2";
    penwidth=2;
    
    // I2C Devices
    subgraph cluster_i2c {
      label="I2C Bus";
      style=filled;
      fillcolor="#BBDEFB";
      color="#1565C0";
      
      ads1115 [label=<<B>ADS1115</B><BR/>ADC>, shape=box, fillcolor="#4FC3F7", fontcolor=white];
      pcf_leds [label=<<B>PCF8574</B><BR/>LED Driver>, shape=box, fillcolor="#4FC3F7", fontcolor=white];
      pcf_relays [label=<<B>PCF8574</B><BR/>Relay Driver>, shape=box, fillcolor="#4FC3F7", fontcolor=white];
    }
    
    // UART Devices
    uart_aqm [label=<<B>PMS1003</B><BR/>Air Quality<BR/>Monitor>, shape=box, fillcolor="#66BB6A", fontcolor=white];
    
    // GPIO
    gpio [label=<<B>GPIO</B><BR/>Direct I/O>, shape=box, fillcolor="#FFA726", fontcolor=white];
  }
  
  // Task Layer
  subgraph cluster_tasks {
    label=<<B>Control Tasks (Async)</B>>;
    style=filled;
    fillcolor="#FFF3E0";
    color="#F57C00";
    penwidth=2;
    
    // Sensing Tasks
    subgraph cluster_sensors {
      label="Sensors";
      style=filled;
      fillcolor="#FFE0B2";
      
      adc_watch [label=<<B>ADC Watch</B><BR/>Saw &amp; Lathe<BR/>Current Sensors>, fillcolor="#FFB74D"];
      aqm_reader [label=<<B>AQM Reader</B><BR/>Particulate<BR/>Monitoring>, fillcolor="#FFB74D"];
    }
    
    // Control Tasks
    subgraph cluster_controllers {
      label="Controllers";
      style=filled;
      fillcolor="#FFE0B2";
      
      saw_gate [label=<<B>Saw Gate</B><BR/>Gate Control>, fillcolor="#81C784"];
      lathe_gate [label=<<B>Lathe Gate</B><BR/>Gate Control>, fillcolor="#81C784"];
      collector_ssr [label=<<B>Collector SSR</B><BR/>Main Fan Control>, fillcolor="#81C784"];
    }
    
    // Policy/Logic Tasks
    subgraph cluster_policy {
      label="Policy & Logic";
      style=filled;
      fillcolor="#FFE0B2";
      
      aqm_policy [label=<<B>AQM Policy</B><BR/>Air Quality<BR/>Rules>, fillcolor="#AED581"];
      aqm_announcer [label=<<B>AQM Announcer</B><BR/>Status Updates>, fillcolor="#AED581"];
    }
  }
  
  // Event Types
  subgraph cluster_events {
    label=<<B>Event Types</B>>;
    style=filled;
    fillcolor="#F3E5F5";
    color="#7B1FA2";
    penwidth=2;
    
    saw_on [label="saw.on", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
    saw_off [label="saw.off", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
    lathe_on [label="lathe.on", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
    lathe_off [label="lathe.off", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
    aqm_metrics [label="aqm.metrics", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
    sys_any_active [label="system.any_active", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
  }
  
  // Hardware connections
  ads1115 -> adc_watch [label="I2C", color="#1976D2", penwidth=2];
  pcf_leds -> saw_gate [label="I2C", color="#1976D2", style=dashed];
  pcf_leds -> lathe_gate [label="I2C", color="#1976D2", style=dashed];
  pcf_relays -> saw_gate [label="I2C", color="#1976D2", penwidth=2];
  pcf_relays -> lathe_gate [label="I2C", color="#1976D2", penwidth=2];
  uart_aqm -> aqm_reader [label="UART", color="#43A047", penwidth=2];
  gpio -> collector_ssr [label="Direct", color="#FB8C00", penwidth=2];
  
  // Event publishing
  adc_watch -> saw_on [color="#E91E63", penwidth=2, label="publish"];
  adc_watch -> saw_off [color="#E91E63", penwidth=2, label="publish"];
  adc_watch -> lathe_on [color="#E91E63", penwidth=2, label="publish"];
  adc_watch -> lathe_off [color="#E91E63", penwidth=2, label="publish"];
  aqm_reader -> aqm_metrics [color="#E91E63", penwidth=2, label="publish"];
  
  // Events through bus
  saw_on -> event_bus [color="#E91E63", style=dashed];
  saw_off -> event_bus [color="#E91E63", style=dashed];
  lathe_on -> event_bus [color="#E91E63", style=dashed];
  lathe_off -> event_bus [color="#E91E63", style=dashed];
  aqm_metrics -> event_bus [color="#E91E63", style=dashed];
  sys_any_active -> event_bus [color="#E91E63", style=dashed];
  
  // Event subscription
  event_bus -> saw_gate [color="#7CB342", penwidth=2, label="subscribe"];
  event_bus -> lathe_gate [color="#7CB342", penwidth=2, label="subscribe"];
  event_bus -> collector_ssr [color="#7CB342", penwidth=2, label="subscribe"];
  event_bus -> aqm_policy [color="#7CB342", penwidth=2, label="subscribe"];
  event_bus -> aqm_announcer [color="#7CB342", penwidth=2, label="subscribe"];
  
  // Legend
  subgraph cluster_legend {
    label="Legend";
    style=filled;
    fillcolor=white;
    color=gray;
    
    leg_pub [label="Publish", shape=plaintext];
    leg_sub [label="Subscribe", shape=plaintext];
    leg_hw [label="Hardware", shape=plaintext];
    
    leg_pub -> leg_sub [color="#E91E63", penwidth=2, label="Event Flow"];
    leg_sub -> leg_hw [color="#1976D2", penwidth=2, label="Hardware I/O"];
  }
}
'''


def generate_dataflow_diagram() -> str:
    """Generate a data flow focused diagram."""
    
    return '''digraph DataFlow {
  rankdir=LR;
  bgcolor="#fafafa";
  fontname="Arial";
  
  node [fontname="Arial", fontsize=11, style=filled];
  edge [fontname="Arial", fontsize=9];
  
  labelloc=t;
  label=<<B><FONT POINT-SIZE="16">Data Flow: Tool Detection → Fan Control</FONT></B>>;
  
  // Input sensors
  subgraph cluster_input {
    label="Physical Inputs";
    style=filled;
    fillcolor="#E8F5E9";
    color="#388E3C";
    penwidth=2;
    
    saw_current [label="Saw\nCurrent Sensor", shape=box, fillcolor="#66BB6A"];
    lathe_current [label="Lathe\nCurrent Sensor", shape=box, fillcolor="#66BB6A"];
    air_sensor [label="Particulate\nSensor", shape=box, fillcolor="#66BB6A"];
  }
  
  // ADC
  adc [label=<<B>ADS1115</B><BR/>Analog to Digital>, shape=box, fillcolor="#42A5F5", fontcolor=white];
  
  // Processing
  subgraph cluster_process {
    label="Signal Processing";
    style=filled;
    fillcolor="#FFF9C4";
    color="#F57F17";
    penwidth=2;
    
    hysteresis [label="Hysteresis\nFiltering", shape=box, fillcolor="#FFEB3B"];
    debounce [label="Debounce\n(3 samples)", shape=box, fillcolor="#FFEB3B"];
  }
  
  // Event generation
  events [label="Events:\nsaw.on/off\nlathe.on/off", shape=ellipse, fillcolor="#BA68C8", fontcolor=white];
  
  // Event bus
  bus [label="Event Bus", shape=cylinder, fillcolor="#EF5350", fontcolor=white];
  
  // Controllers
  subgraph cluster_control {
    label="Gate Controllers";
    style=filled;
    fillcolor="#E1F5FE";
    color="#0277BD";
    penwidth=2;
    
    saw_ctrl [label="Saw Gate\nController", shape=box, fillcolor="#29B6F6"];
    lathe_ctrl [label="Lathe Gate\nController", shape=box, fillcolor="#29B6F6"];
  }
  
  // Outputs
  subgraph cluster_output {
    label="Physical Outputs";
    style=filled;
    fillcolor="#FCE4EC";
    color="#C2185B";
    penwidth=2;
    
    saw_gate [label="Saw\nBlast Gate", shape=box, fillcolor="#EC407A"];
    lathe_gate [label="Lathe\nBlast Gate", shape=box, fillcolor="#EC407A"];
    collector [label="Dust Collector\nFan", shape=box, fillcolor="#EC407A"];
    leds [label="Status\nLEDs", shape=box, fillcolor="#EC407A"];
  }
  
  // Connections
  saw_current -> adc [penwidth=2];
  lathe_current -> adc [penwidth=2];
  
  adc -> hysteresis [penwidth=2, label="10Hz"];
  hysteresis -> debounce [penwidth=2];
  debounce -> events [penwidth=2, label="state change"];
  
  events -> bus [penwidth=2];
  
  bus -> saw_ctrl [penwidth=2];
  bus -> lathe_ctrl [penwidth=2];
  
  saw_ctrl -> saw_gate [penwidth=2, label="open/close"];
  lathe_ctrl -> lathe_gate [penwidth=2, label="open/close"];
  
  saw_ctrl -> leds [style=dashed, label="green/red"];
  lathe_ctrl -> leds [style=dashed, label="green/red"];
  
  bus -> collector [penwidth=2, style=dashed, label="any tool active"];
  
  air_sensor -> bus [penwidth=2, color="#43A047", label="aqm.metrics"];
}
'''


def generate_state_diagram() -> str:
    """Generate a state machine diagram for gate control."""
    
    return '''digraph GateStateMachine {
  rankdir=LR;
  bgcolor="#f5f5f5";
  fontname="Arial";
  
  node [fontname="Arial", fontsize=11, style=filled, shape=circle];
  edge [fontname="Arial", fontsize=9];
  
  labelloc=t;
  label=<<B><FONT POINT-SIZE="16">Blast Gate State Machine</FONT></B>>;
  
  // States
  closed [label=<<B>CLOSED</B><BR/><FONT POINT-SIZE="9">LED: RED<BR/>Relay: OFF</FONT>>, 
          fillcolor="#EF5350", fontcolor=white, penwidth=3];
  
  opening [label=<<B>OPENING</B><BR/><FONT POINT-SIZE="9">Relay: OPEN<BR/>Timer: 6s</FONT>>, 
           fillcolor="#FFA726", fontcolor=white];
  
  open [label=<<B>OPEN</B><BR/><FONT POINT-SIZE="9">LED: GREEN<BR/>Relay: OFF</FONT>>, 
        fillcolor="#66BB6A", fontcolor=white, penwidth=3];
  
  closing [label=<<B>CLOSING</B><BR/><FONT POINT-SIZE="9">Relay: CLOSE<BR/>Timer: 6s</FONT>>, 
           fillcolor="#FFA726", fontcolor=white];
  
  // State transitions
  closed -> opening [label=<<I>tool.on</I>>, penwidth=2, color="#4CAF50"];
  opening -> open [label="timer expired", penwidth=2];
  
  open -> closing [label=<<I>tool.off</I>>, penwidth=2, color="#F44336"];
  closing -> closed [label="timer expired", penwidth=2];
  
  // Cancel transitions
  opening -> closing [label=<<I>tool.off</I><BR/>(cancel)>, style=dashed, color=red];
  closing -> opening [label=<<I>tool.on</I><BR/>(cancel)>, style=dashed, color=green];
  
  // Initial state
  start [shape=point, width=0.3, fillcolor=black];
  start -> closed [penwidth=2];
  
  // Notes
  note [shape=note, label=<<B>Notes:</B><BR ALIGN="LEFT"/>
• 0.1s deadtime between relay transitions<BR ALIGN="LEFT"/>
• Max 6s drive time prevents overheating<BR ALIGN="LEFT"/>
• Relay lock prevents conflicts<BR ALIGN="LEFT"/>>, 
        fillcolor="#FFFDE7", style=filled];
}
'''


def main():
    print("Generating enhanced diagrams...")
    
    # Enhanced system diagram
    with open('system_diagram_enhanced.dot', 'w') as f:
        f.write(generate_enhanced_system_diagram())
    print("  -> system_diagram_enhanced.dot")
    
    # Data flow diagram
    with open('dataflow_diagram.dot', 'w') as f:
        f.write(generate_dataflow_diagram())
    print("  -> dataflow_diagram.dot")
    
    # State machine diagram
    with open('state_machine.dot', 'w') as f:
        f.write(generate_state_diagram())
    print("  -> state_machine.dot")
    
    print("\nDone! Use 'dot -Tpng <file>.dot -o <file>.png' to generate images.")


if __name__ == '__main__':
    main()
