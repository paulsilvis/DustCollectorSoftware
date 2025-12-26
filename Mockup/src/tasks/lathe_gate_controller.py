from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig

log = logging.getLogger(__name__)


async def run_lathe_gate_controller(bus: EventBus) -> None:
    """
    Mock actuator (REVERSED COLORS):

    - lathe.on  -> Gate4 RED solid   (gate "open")
    - lathe.off -> Gate4 GREEN solid (gate "closed")

    Wiring unchanged. Semantics only.
    """
    q = bus.subscribe(maxsize=100)

    cfg = PcfLedsConfig(
        bus=1,
        addr=0x20,
        green_bit=3,  # Gate4 GREEN
        red_bit=7,    # Gate4 RED
        active_low=True,
    )

    leds = PcfLedPair(cfg)

    # Default to "closed"
    leds.set_green()

    try:
        while True:
            ev = await q.get()

            if ev.type == "lathe.on":
                leds.set_red()
                log.info("LATHE CTRL: OPEN (Gate4 RED)")

            elif ev.type == "lathe.off":
                leds.set_green()
                log.info("LATHE CTRL: CLOSE (Gate4 GREEN)")

    except asyncio.CancelledError:
        log.info("Lathe gate controller cancelled")
        raise
    finally:
        leds.close(restore=True)
