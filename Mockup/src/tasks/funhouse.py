from __future__ import annotations
import logging

from ..event_bus import EventBus

log = logging.getLogger("funhouse")


async def funhouse(bus: EventBus, cfg, hw):
    if not cfg.raw["features"]["led_strip"]:
        log.info("funhouse disabled")
        return
    q = bus.subscribe()
    log.info("funhouse started (%s)", "MOCK" if cfg.mock else "REAL")
    while True:
        ev = await q.get()
        if ev.type in ("machine.on", "machine.off"):
            tool = ev.data.get("tool", "?")
            cmd = f"{ev.type}:{tool}\n".encode("utf-8")
            try:
                hw.ser_tx.write(cmd)
            except Exception:
                pass
