from __future__ import annotations
import asyncio
import logging
from ..event_bus import EventBus

log = logging.getLogger("sys_monitor")


async def sys_monitor(bus: EventBus, cfg, hw):
    _ = bus.subscribe()  # currently unused
    log.info("sys_monitor started (stub)")
    while True:
        await asyncio.sleep(5)
