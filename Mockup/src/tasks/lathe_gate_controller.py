from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig

log = logging.getLogger(__name__)


async def run_lathe_gate_controller(bus: EventBus) -> None:
    """
    Gate4 LED actuator controller (PCF8574).

    Semantics:
    - lathe.on  -> GREEN solid  (gate "open"/running)
    - lathe.off -> RED solid    (gate "closed"/stopped)

    Note: The PCF8574 board wiring is swapped relative to our initial assumption,
    so green/red bits are swapped here to match physical LED colors.
    """
    q = bus.subscribe(maxsize=100)

    cfg = PcfLedsConfig(
        bus=1,
        addr=0x20,
        green_bit=7,  # swapped
        red_bit=3,    # swapped
        active_low=True,
    )

    leds = PcfLedPair(cfg)

    # Default state: assume lathe is OFF at boot
    leds.set_red()
    log.info("LATHE CTRL: boot -> CLOSED (Gate4 RED)")

    try:
        while True:
            ev = await q.get()

            if ev.type == "lathe.on":
                leds.set_green()
                log.info("LATHE CTRL: OPEN (Gate4 GREEN)")

            elif ev.type == "lathe.off":
                leds.set_red()
                log.info("LATHE CTRL: CLOSE (Gate4 RED)")

            else:
                # Keep this noisy log OFF unless debugging.
                # log.debug("LATHE CTRL: ignoring event type=%s src=%s", ev.type, ev.src)
                pass

    except asyncio.CancelledError:
        log.info("Lathe gate controller cancelled")
        raise
    finally:
        # Best-effort cleanup; do not crash shutdown if I2C is unhappy.
        try:
            leds.close(restore=False)
        except Exception:
            log.exception("Lathe controller: failed to close LEDs")
