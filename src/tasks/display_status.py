from __future__ import annotations
import logging
from ..event_bus import EventBus

log = logging.getLogger("display_status")


async def display_status(bus: EventBus, cfg, hw):
    q = bus.subscribe()
    log.info("display_status started")
    while True:
        ev = await q.get()
        # keep this quiet unless you want chatty output
        if ev.type in ("machine.on", "machine.off", "system.any_active", "aqm.good", "aqm.bad"):
            log.debug("status: %s %s", ev.type, ev.data)
