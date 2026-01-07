from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass

from ..event_bus import EventBus

log = logging.getLogger("gate_controller")


@dataclass
class Gate:
    fwd_bit: int
    rev_bit: int
    led_red: int
    led_green: int


def _gate_from_cfg(d: dict) -> Gate:
    return Gate(
        fwd_bit=int(d["fwd_bit"]),
        rev_bit=int(d["rev_bit"]),
        led_red=int(d["led_red"]),
        led_green=int(d["led_green"]),
    )


async def _move_gate(hw, g: Gate, open_: bool, dead_ms: int, timeout_s: int):
    # Direction exclusion (belt & suspenders)
    hw.relays_stop_gate(g.fwd_bit, g.rev_bit)

    if dead_ms > 0:
        await asyncio.sleep(dead_ms / 1000)

    # Drive one direction only
    bit = g.fwd_bit if open_ else g.rev_bit
    hw.relays_drive(bit, active_low_on=True)

    # LEDs: open=green, closed=red (active-low sink)
    hw.led_set_pair(g.led_red, g.led_green, red_on=not open_, green_on=open_)

    try:
        # Internal actuator limit switches stop travel; timeout is just a hard stop.
        await asyncio.sleep(timeout_s)
    finally:
        hw.relays_stop_gate(g.fwd_bit, g.rev_bit)


async def gate_controller(bus: EventBus, cfg, hw):
    q = bus.subscribe()
    gates_cfg = cfg.raw["gates"]["map"]
    gates = {name: _gate_from_cfg(gates_cfg[name]) for name in gates_cfg}

    dead_ms = int(cfg.raw["gates"]["dead_time_ms"])
    timeout_s = int(cfg.raw["gates"]["move_timeout_s"])

    # Per-gate arbitration: prevents conflicting open/close overlap on the SAME gate,
    # but allows different gates to move concurrently.
    gate_locks = {name: asyncio.Lock() for name in gates}

    log.info("gate_controller ready (arb=per_gate_lock, relays=atomic_masked_updates)")
    while True:
        ev = await q.get()
        if ev.type not in ("machine.on", "machine.off"):
            continue

        tool = ev.data.get("tool")
        g = gates.get(tool)
        if not g:
            continue

        open_ = ev.type == "machine.on"
        log.info("%s gate for %s", "Opening" if open_ else "Closing", tool)

        async def runner(name: str, gate: Gate, do_open: bool):
            async with gate_locks[name]:
                await _move_gate(hw, gate, do_open, dead_ms, timeout_s)

        asyncio.create_task(runner(tool, g, open_))
