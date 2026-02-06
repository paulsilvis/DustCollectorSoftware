from __future__ import annotations

import asyncio

from ..event_bus import EventBus
from ..hardware.pcf_relays import PcfRelays
from .base_gate_controller import BaseGateController, GateConfig

# LED bits on PCF @ 0x20
LATHE_LED_GREEN_BIT = 7
LATHE_LED_RED_BIT = 3

# Relay bits on PCF @ 0x21
# Canonical convention (empirically verified):
#   odd bit  = CLOSE
#   even bit = OPEN
LATHE_RELAY_CLOSE_BIT = 5
LATHE_RELAY_OPEN_BIT = 4


async def run_lathe_gate_controller(
    bus: EventBus,
    relays: PcfRelays,
    relay_lock: asyncio.Lock,
) -> None:
    """
    Lathe gate controller.

    Events:
      lathe.on  -> LED GREEN, drive OPEN for MAX_DRIVE_S, then stop
      lathe.off -> LED RED,   drive CLOSE for MAX_DRIVE_S, then stop

    relay_lock MUST be shared across all controllers touching relays@0x21.
    """
    config = GateConfig(
        name="lathe",
        event_on="lathe.on",
        event_off="lathe.off",
        led_green_bit=LATHE_LED_GREEN_BIT,
        led_red_bit=LATHE_LED_RED_BIT,
        relay_open_bit=LATHE_RELAY_OPEN_BIT,
        relay_close_bit=LATHE_RELAY_CLOSE_BIT,
    )

    controller = BaseGateController(bus, relays, relay_lock, config)
    await controller.run()
