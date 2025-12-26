from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from ..config_loader import AppConfig
from ..event_bus import EventBus
from ..hardware.gpio import GPIOOut
from ..hardware.mock_hw import MockGPIOOut

log = logging.getLogger(__name__)


class GPIOOutLike(Protocol):
    def write(self, on: bool) -> None: ...


async def collector_controller(bus: EventBus, cfg: AppConfig, hw: object) -> None:
    # GPIO pin comes from config raw dict
    pin = int(cfg.raw["gpio"]["collector_ssr"])

    ssr: GPIOOutLike = MockGPIOOut(pin, active_high=True) if cfg.mock else GPIOOut(
        pin, active_high=True
    )

    ssr.write(False)
    log.info("collector_controller ready (OFF by default)")

    q = bus.subscribe()
    collector_on = False

    while True:
        evt = await q.get()
        if evt.type == "collector.on" and not collector_on:
            ssr.write(True)
            collector_on = True
            log.info("Collector ON")
        elif evt.type == "collector.off" and collector_on:
            ssr.write(False)
            collector_on = False
            log.info("Collector OFF")
        await asyncio.sleep(0)
