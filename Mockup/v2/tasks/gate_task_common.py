from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from ..domain.gate import Gate
from ..domain.leds import Leds
from ..system.event_bus import EventBus, DeviceEvent

log = logging.getLogger(__name__)


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

    Listens for DeviceEvent(name=<device>, kind="on"/"off") and drives:
      - gate.open() / gate.close()
      - LEDs for on/off state

    This is pure policy: no I2C, no hardware details.
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

    try:
        while True:
            ev = await q.get()

            if not isinstance(ev, DeviceEvent):
                # Ignore unknown event types
                continue

            if ev.name != cfg.device_name:
                continue

            if ev.kind == "on":
                await gate.open()
                await set_led_state(True)

            elif ev.kind == "off":
                await gate.close()
                await set_led_state(False)
    except asyncio.CancelledError:
        log.info("Gate task for %s cancelled, shutting down", cfg.device_name)
        # Optional: de-energize relays, set LEDs to a safe state, etc.
        try:
            await gate.stop()
        except Exception:
            log.exception("Error while stopping gate %s during cancellation", cfg.device_name)
        raise
