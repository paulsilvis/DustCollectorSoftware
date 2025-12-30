from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ..domain.gate import Gate
from ..domain.leds import Leds
from ...src.event_bus import EventBus   # reusing your existing bus events


@dataclass
class GateTaskConfig:
    device_name: str
    on_led: int
    off_led: int
    open_time_s: float = 6.0
    close_time_s: float = 6.0


async def run_gate_task(
    bus: EventBus,
    gate: Gate,
    leds: Leds,
    cfg: GateTaskConfig,
) -> None:
    """
    Shared controller loop for a single gate.

    Listens for:
        DeviceOn(name)
        DeviceOff(name)

    And drives:
        - gate open/close
        - LED on/off representation
    """

    q = bus.subscribe(maxsize=20)

    async def set_led_state(is_on: bool) -> None:
        if is_on:
            await leds.on(cfg.on_led)
            await leds.off(cfg.off_led)
        else:
            await leds.off(cfg.on_led)
            await leds.on(cfg.off_led)

    # Initial LED state = OFF
    await set_led_state(False)

    while True:
        ev = await q.get()

        # You already use named events, so we reuse them
        if getattr(ev, "name", None) != cfg.device_name:
            continue

        # Device turned ON
        if ev.kind == "on":
            await gate.open()
            await set_led_state(True)

        # Device turned OFF
        elif ev.kind == "off":
            await gate.close()
            await set_led_state(False)
