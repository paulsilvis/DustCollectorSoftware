# DustCollector Software – Design Overview

## Purpose

This system automatically controls blast gates and a dust collector
based on which shop machines are drawing current. It is designed to
be deterministic, observable, and testable without hardware.

## High-Level Architecture

The system is composed of independent asyncio tasks that communicate
exclusively through an event bus.

    ADC Watch ──▶ Machine Events ──▶ Gate Controller
                                └─▶ Collector Controller

No task directly calls another task.

## Core Concepts

### Event Bus

A simple pub/sub message bus.
- Producers emit string events (e.g. `machine.on:drill`)
- Consumers subscribe using integer topic IDs
- Delivery is ordered and non-blocking

### Machine Detection

`adc_watch` simulates or reads current sensors.
Threshold crossings generate:

    machine.on:<name>
    machine.off:<name>

These events are also echoed to the mock ESP32 for visibility.

### Gate Control

`gate_controller` listens for machine events and:
- Opens the corresponding blast gate
- Closes gates when machines turn off
- Uses per-gate locks so unrelated gates can move concurrently
- Writes to relay expanders using atomic masked updates

### Collector Control

`collector_controller` listens for *any* machine activity.
- Turns the collector ON when the first machine starts
- Turns it OFF after all machines are idle
- No unnecessary delays or global locks

### Mock vs Hardware

All hardware is accessed through narrow interfaces.
When `MOCK=true`:
- GPIO, ADC, PCF8574, PMS1003 are simulated
- Waveforms can be `realistic` or `pathological`
- Logs show exactly what *would* be written

## Logging Philosophy

- Logs are the primary debugging interface
- Events are always visible
- Wrapped lines are indented for readability
- No semantic changes occur due to logging

## Design Goals

- Deterministic behavior
- Minimal coupling
- Hardware-free testing
- Clear, boring correctness

This system favors clarity over cleverness.
