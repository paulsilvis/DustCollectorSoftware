from __future__ import annotations

import asyncio
import logging

from ..config_loader import AppConfig
from ..event_bus import EventBus

log = logging.getLogger("collector_controller")


async def collector_controller(bus: EventBus, cfg: AppConfig, hw: object) -> None:
    """
    Collector SSR control.

    This controller listens to the system-level aggregation event:

        system.any_active  { value: bool, active: [tool, ...] }

    and turns the collector SSR ON when value=True and OFF when value=False.

    Rationale:
    - machine_manager already owns "which tools are active?"
    - collector_controller should simply actuate the collector accordingly
    - no need for separate collector.on/off events
    """
    _ = cfg  # reserved for future: overrun timers, etc.

    ssr = getattr(hw, "gpio25", None)
    if ssr is None:
        raise RuntimeError("Hardware object missing gpio25 (collector SSR output)")

    # OFF by default
    hw.gpio_set_ssr(ssr, False)
    collector_on = False
    log.info("collector_controller ready (OFF by default)")

    q = bus.subscribe()

    while True:
        evt = await q.get()

        if getattr(evt, "type", None) != "system.any_active":
            continue

        data = getattr(evt, "data", {}) or {}
        want_on = bool(data.get("value", False))
        active = data.get("active", [])

        if want_on and not collector_on:
            hw.gpio_set_ssr(ssr, True)
            collector_on = True
            log.info("Collector ON (active=%s)", active)
        elif (not want_on) and collector_on:
            hw.gpio_set_ssr(ssr, False)
            collector_on = False
            log.info("Collector OFF")

        await asyncio.sleep(0)
