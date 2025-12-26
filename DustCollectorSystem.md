---
title: Dust Collector System
tags: [dust-collection, raspberry-pi, workshop-automation, project]
created: 2025-10-18
updated: 2025-10-18
author: Paul Silvis
description: Comprehensive documentation for the automated Dust Collector system, including hardware, software, and coordination contracts.
---

> [!summary]
> This document describes the Dust Collector System designed for Paul's workshop. It covers design concepts, hardware, implementation, and coordination contracts. The goal is a maintainable, documented system suitable for long-term use and expansion.

```table-of-contents
title: Table of Contents
style: nestedList
minLevel: 2
maxLevel: 4
includeLinks: true
hideWhenEmpty: false
```

## Overview

The major purpose of this system is to control a dust collector motor and the associated blast gates in the duct system automatically, based on whether or not a particular connected machine (e.g., the tablesaw) is turned on or off.

As soon as a connected machine is switched on, the dust collector motor/impeller is turned on and the appropriate blast gate is opened. When that machine is turned off, the corresponding gate is closed, and if there are no other connected machines running, the dust collector motor/impeller will be turned off.

Additionally, there are background tasks such as:

- Flashing LED strip patterns to amuse grandchildren
- Status LEDs for visual confirmation of gate state
- Air-quality monitoring and remediation
- Status display on various devices
- Live stream from the ISS (because “why not”)
- Sound effects for motor spin-up/spin-down
- Button- and switch-triggered events for fun

---

## Concepts

### Blast Gates
Home-made, self-cleaning “air switches” that open or close a specific duct. Controlled by linear actuators.

### Machines
Dust-producing machines connected to the system:

- Tablesaw
- Lathe
- Drill press
- Spare (bench vac or router)

### Displays
Fun and functional methods for presenting system information using available screens.

### Dust Collector
1½ HP impeller motor moving air at ~85 MPH through a 5" duct. Cyclone separator drops heavy material into a bin and fine dust into a pleated filter.

### Air Quality Monitor
This is a sensor that draws air from the room and determines the amount of fine particulate matter in the air.  If it exceeds a 'safe' limit, the fan for a Corsi-Rosenthal air filter is started to bring the level of particulate matter down to a safe level

## Hardware

### Current Sensors
Split-core transformers around the hot leg of each machine feed. They provide ~1 V AC signals converted to 0–1 V DC via conditioning circuits, then read by ADC channels and debounced.

### ADC
ADS1115 (I²C, 0x48). Four channels:
- 0 — Tablesaw
- 1 — Lathe
- 2 — Drill press
- 3 — Spare (bench vac/router)

### LCD
Sainsmart LCD2004 (4×20) at I²C 0x3F. Auxiliary log and display.

### OLED
SSD1306 (I²C 0x3C). Displays numeric or graphical air-quality data.

### HDMI Display
Small display used as Raspberry Pi console and optional ISS feed output.

### LED Strip
Off-board ESP32-controlled WS2812B strip. Receives serial commands for on/off and pattern control.

### LED Bank
Eight LEDs (4 red, 4 green) to indicate gate states (open = green, closed = red). Controlled by PCF8574 @ 0x20.

### Air Quality Monitor (PMS1003)
Serial output (~1 Hz). Data controls the OLED and Corsi–Rosenthal filter fan.

### Filter Fan
Triggered by SSR when air-quality degrades.

### Dust Collector Impeller
Main motor, controlled via GPIO 25 → SSR (High = ON).

### Digital Bus
Five PCF8574 chips (0x20–0x24). Configurable I/O bits; some connected to DB‑25 connectors on the enclosure.

### Relays

#### Fan Relay
Not yet implemented — fan runs continuously.

#### Actuator Relays
8‑relay board controlled by PCF8574 @ 0x21 for actuator H‑bridge operation.

### Linear Actuators
Operate blast gates via H‑bridge. Built‑in limit switches prevent over‑travel.

---

## Implementation

System runs on Raspberry Pi 4B (Debian 12) using Python 3 + `asyncio` for multitasking. The Pi easily handles workload and “funhouse” extras.

### Coding Style

> [!tip]
> Follow PEP 8, minimize abstraction, and prefer clear, direct behavior over unnecessary indirection.

- Keep design pragmatic and readable.
- Avoid over‑engineering.
- Reference [this chat](https://chatgpt.com/share/68f31304-e914-8001-9520-736ced32dcd1) when uncertain.

### Tasks

- Monitor ADC and emit `machine.on/off` events on threshold crossings.
- React to machine events by controlling gates, collector motor, LEDs, and logs.  
  _Actions may span several seconds and involve multiple internal states._
- Decode PMS1003 messages to control OLED and fan.
- Monitor Pi temperature and drive enclosure fan with hysteresis.
- Monitor sawdust bin ToF sensor and control alarm light.
- Maintain HDMI ISS stream and auto‑restart if disconnected.
- Display events and system states on LCD/OLED/HDMI as needed.

---

## I²C Address Map

| Name                           | Device             | Address  | Function                              |
|--------------------------------|--------------------|-----------|----------------------------------------|
| LCD                            | Sainsmart LCD2004  | 0x3F      | Utility log display                    |
| OLED                           | SSD1306            | 0x3C      | Air quality display                    |
| Digital Bus                    | PCF8574            | 0x20      | LED bank                               |
| Actuator Control               | PCF8574            | 0x21      | Relay H‑bridge                         |
| Spare I/O                      | PCF8574            | 0x22–0x24 | Extra I/O                              |
| LED Strip                      | ESP32 (off‑board)  | GPIO Tx   | Serial LED control                     |
| ADC                            | ADS1115            | 0x48      | Reads current sensors                  |
| Dust Collector Relay           | SSR                | GPIO 25   | High = ON                              |
| Fan Relay                      | SSR                | GPIO 24   | High = ON                              |
| AQM Sensor                     | PMS1003            | GPIO Rx   | Serial air‑quality input               |

---

## Bob’s Contract

### Hardware Interface Contract v0.2

#### I²C Bus
- 0x3F — LCD2004  
- 0x3C — SSD1306 OLED  
- 0x48 — ADS1115 ADC  
- 0x20–0x24 — PCF8574s (LEDs, relays, spares)  
- Pull‑ups: 2.2–10 kΩ to 3.3 V

#### GPIO / UART (BCM)
- GPIO 25 → SSR Dust Collector (High = ON)  
- GPIO 24 → SSR Filter Fan (High = ON)  
- UART0 @ 9600 bps → TXD0→ESP32, RXD0←PMS1003  
- Disable serial console, enable UART hardware.

#### PCF8574 Bit Maps
- **0x20 — LED Bank**: b0 TS RED, b1 TS GREEN, b2 Lathe RED, b3 Lathe GREEN, b4 Drill RED, b5 Drill GREEN, b6 Spare RED, b7 Spare GREEN. Never drive RED + GREEN simultaneously.  
- **0x21 — Actuator H‑Bridge**: b0 TS FWD, b1 TS REV, b2 Lathe FWD, b3 Lathe REV, b4 Drill FWD, b5 Drill REV, b6 Spare FWD, b7 Spare REV. Interlocks: no FWD+REV; 150–300 ms dead‑time; 6–8 s timeout.

#### Boot‑Safe Rules
On startup: initialize I²C, set directions, set all relays OFF, SSRs OFF, LEDs known; wait ≥ 200 ms before motion. Relays must power idle (PCF8574 defaults HIGH).

#### ADC Acquisition
ADS1115 ±4.096 V FS, ≥128 SPS, rolling average. Tune empirically.

#### SSRs / Power
Collector SSR must handle inductive load with heatsink. Fan SSR zero‑cross OK. Use star ground and isolate AC/logic. Add ULN2803A if relay inputs > 2 mA.

---

### Software Coordination Contract v0.2

####  Event Primitive
```python
@dataclass
class Event:
    type: str      # "machine.on", "machine.off", ...
    src: str       # "adc.tablesaw", etc.
    ts: float
    data: dict
```
Single `asyncio.Queue[Event]` shared by all tasks.

#### Core Tasks
- **adc_watch** – Reads ADS1115, debounces, emits `machine.on/off`.  
- **machine_manager** – Tracks active tools; emits `system.any_active`.  
- **gate_controller** – Operates gates and handles timeouts.  
- **collector_controller** – Turns collector ON when any machine active, OFF otherwise.  
- **aqm_reader** – Reads PMS1003 @ 9600 bps; emits `aqm.bad/good`.  
- **display_status** – Updates LCD/OLED/LED bank.  
- **sys_monitor** – Manages temperature and safety locks.  
- **funhouse** – Handles ESP32 LED/sound effects.

####  Debounce State Machine
- `ON_threshold` ≥ 300 ms → `machine.on`  
- `OFF_threshold` ≥ 800–1000 ms → `machine.off`  
- Hysteresis: ON > OFF.

#### Faults / Safety
Actuator timeout or FWD+REV error → drop relays, set fault flag.  
Severe AQM/over‑temp → pause Funhouse only.  
systemd watchdog ensures safe defaults.

---

### Minimal To‑Do
1. Verify relay polarity and current; add ULN2803A if needed.  
2. Lock UART @ 9600 bps; disable console.  
3. Implement per‑tool debounce + `system.any_active`.  
4. Add interlocks and timeouts.  
5. Test boot‑safe sequence.