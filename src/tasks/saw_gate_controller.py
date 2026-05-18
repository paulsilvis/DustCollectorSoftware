from __future__ import annotations

import asyncio

from ..config_loader import AppConfig
from ..event_bus import EventBus
from ..hardware.pcf_relays import PcfRelays
from .base_gate_controller import BaseGateController, GateConfig

# LED bits on PCF @ 0x20
SAW_LED_GREEN_BIT = 6
SAW_LED_RED_BIT = 2

# Relay bits on PCF @ 0x21
# Canonical convention (empirically verified):
# bit 7 = CLOSE, bit 6 = OPEN
SAW_RELAY_CLOSE_BIT = 7
SAW_RELAY_OPEN_BIT = 6


async def run_saw_gate_controller(
    bus: EventBus,
    relays: PcfRelays,
    relay_lock: asyncio.Lock,
    app_cfg: AppConfig,
) -> None:
    """
    Saw gate controller.

    Timing is owned by the tool_announcer: audio plays first, then
    .ready events are published. Gate acts immediately on those.

      saw.on.ready  -> LED GREEN, drive OPEN for MAX_DRIVE_S then stop
      saw.off.ready -> LED RED,   drive CLOSE for MAX_DRIVE_S then stop

    relay_lock MUST be shared across all controllers using relays@0x21.
    """
    config = GateConfig(
        name="saw",
        event_on="saw.on.ready",
        event_off="saw.off",
        led_green_bit=SAW_LED_GREEN_BIT,
        led_red_bit=SAW_LED_RED_BIT,
        relay_open_bit=SAW_RELAY_OPEN_BIT,
        relay_close_bit=SAW_RELAY_CLOSE_BIT,
        gate_delay_s=0.0,
    )

    controller = BaseGateController(bus, relays, relay_lock, config)
    await controller.run()
