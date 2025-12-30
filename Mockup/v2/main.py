from __future__ import annotations

import asyncio
import logging

from .hardware.pcf8574 import Pcf8574, open_default_bus
from .hardware.relays import RelayBank
from .hardware.leds_hw import LedBank
from .domain.gate import Gate
from .domain.leds import Leds

from ..src.event_bus import EventBus
from .tasks.saw_gate_task import run_saw_gate_controller
from .tasks.lathe_gate_task import run_lathe_gate_controller


log = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

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
    #   Adjust bit numbers to EXACTLY match your wiring
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
    # EventBus
    # ---------------------------------------------------------
    bus_events = EventBus()

    tasks = [
        asyncio.create_task(run_saw_gate_controller(bus_events, saw_gate, leds)),
        asyncio.create_task(run_lathe_gate_controller(bus_events, lathe_gate, leds)),
    ]

    log.info("V2 system running...")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
