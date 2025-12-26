from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus

log = logging.getLogger(__name__)


async def run_lathe_gate_controller(bus: EventBus) -> None:
    """
    Stub controller: listens for lathe.on/off and logs intended actions.

    No motors, no relays, no sound. This is purely the behavioral glue.
    """
    q = bus.subscribe(maxsize=100)

    try:
        while True:
            ev = await q.get()

            if ev.type == "lathe.on":
                log.info("LATHE CTRL: would OPEN lathe gate (event=%s)", ev.type)

            elif ev.type == "lathe.off":
                log.info("LATHE CTRL: would CLOSE lathe gate (event=%s)", ev.type)

    except asyncio.CancelledError:
        log.info("Lathe gate controller cancelled")
        raise
