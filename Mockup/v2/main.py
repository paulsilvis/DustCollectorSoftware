from __future__ import annotations

import asyncio
import logging

from .domain.gate import Gate
from .domain.leds import Leds
from .hardware.leds_hw import LedBank
from .hardware.pcf8574 import Pcf8574, open_default_bus
from .hardware.relays import RelayBank
from .system.event_bus import EventBus
from .tasks.lathe_gate_task import run_lathe_gate_controller
from .tasks.saw_gate_task import run_saw_gate_controller

log = logging.getLogger(__name__)


async def _run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

    # ---------------------------------------------------------
    # Hardware setup
    # ---------------------------------------------------------
    bus = open_default_bus()

    pcf_leds = Pcf8574(bus, addr=0x20)
    pcf_relays = Pcf8574(bus, addr=0x21)

    led_bank = LedBank(pcf_leds)
    relay_bank = RelayBank(pcf_relays)

    leds = Leds(led_bank)

    # ---------------------------------------------------------
    # Gates
    #   Keep these bit numbers EXACTLY matched to your wiring.
    # ---------------------------------------------------------
    saw_gate = Gate(
        name="saw",
        relay_bank=relay_bank,
        open_bit=0,
        close_bit=1,
    )

    lathe_gate = Gate(
        name="lathe",
        relay_bank=relay_bank,
        open_bit=2,
        close_bit=3,
    )

    # ---------------------------------------------------------
    # EventBus + tasks
    # ---------------------------------------------------------
    bus_events = EventBus()

    tasks: list[asyncio.Task[None]] = [
        asyncio.create_task(
            run_saw_gate_controller(bus_events, saw_gate, leds),
            name="saw_gate",
        ),
        asyncio.create_task(
            run_lathe_gate_controller(bus_events, lathe_gate, leds),
            name="lathe_gate",
        ),
    ]

    log.info("V2 system running... (NO DEMO PUBLISHER)")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        log.info("Main task cancelled, shutting down tasks")
        raise
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> int:
    try:
        asyncio.run(_run())
        return 0
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
