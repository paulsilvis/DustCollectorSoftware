from __future__ import annotations
import logging
from ..events import Event
from ..event_bus import EventBus

log = logging.getLogger("machine_manager")


async def machine_manager(bus: EventBus):
    q = bus.subscribe()
    active: set[str] = set()
    log.info("machine_manager ready")
    while True:
        ev = await q.get()
        if ev.type == "machine.on":
            tool = ev.data.get("tool")
            if tool:
                active.add(tool)
                await bus.publish(Event.now("system.any_active", "machine_manager", value=True, active=sorted(active)))
        elif ev.type == "machine.off":
            tool = ev.data.get("tool")
            if tool and tool in active:
                active.remove(tool)
            await bus.publish(Event.now("system.any_active", "machine_manager", value=bool(active), active=sorted(active)))
