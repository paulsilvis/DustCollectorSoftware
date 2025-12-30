from __future__ import annotations

import asyncio
import logging

from .hardware.pcf8574 import Pcf8574, open_default_bus
from .hardware.relays import RelayBank
from .hardware.leds_hw import LedBank
from .domain.gate import Gate
from .domain.leds import Leds
from .system.event_bus import EventBus, DeviceEvent
from .tasks.saw_gate_task import run_saw_gate_controller
from .tasks.lathe_gate_task import run_lathe_gate_controller


log = logging.getLogger(__name__)


async def _demo_publisher(bus: EventBus) -> None:
    """
    Temporary demo publisher so we can see gates and LEDs move
    without the ADC watcher wired up yet.
    """
    try:
        while True:
            log.info("DEMO: saw ON")
            await bus.publish(DeviceEvent(name="saw", kind="on"))
            await asyncio.sleep(5.0)

            log.info("DEMO: saw OFF")
            await bus.publish(DeviceEvent(name="saw", kind="off"))
            await asyncio.sleep(5.0)

            log.info("DEMO: lathe ON")
            await bus.publish(DeviceEvent(name="lathe", kind="on"))
            await asyncio.sleep(5.0)

            log.info("DEMO: lathe OFF")
            await bus.publish(DeviceEvent(name="lathe", kind="off"))
            await asyncio.sleep(5.0)
    except asyncio.CancelledError:
        log.info("Demo publisher cancelled, shutting down")
        raise


async def main() -> None:
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
    # EventBus + tasks
    # ---------------------------------------------------------
    bus_events = EventBus()

    tasks = [
        asyncio.create_task(
            run_saw_gate_controller(bus_events, saw_gate, leds),
            name="saw_gate",
        ),
        asyncio.create_task(
            run_lathe_gate_controller(bus_events, lathe_gate, leds),
            name="lathe_gate",
        ),
        asyncio.create_task(
            _demo_publisher(bus_events),
            name="demo_publisher",
        ),
    ]

    log.info("V2 system running...")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        log.info("Main task cancelled, shutting down tasks")
        # Let tasks clean themselves up; they already see CancelledError.
        for t in tasks:
            if not t.done():
                t.cancel()
        # Wait a moment for everything to settle
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Clean, quiet exit on Ctrl-C
        log.info("Keyboard interrupt, exiting cleanly")
