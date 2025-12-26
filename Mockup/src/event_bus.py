from __future__ import annotations

import asyncio
import logging
from typing import Iterable, List

log = logging.getLogger("event_bus")


class EventBus:
    """Simple fan-out bus.

    IMPORTANT: asyncio.Queue is a work queue (one consumer). We need broadcast:
    every subscriber should see every event.
    """

    def __init__(self) -> None:
        self._subs: List[asyncio.Queue] = []

    def subscribe(self, maxsize: int = 0) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subs.append(q)
        return q

    async def publish(self, event) -> None:
        # Fan-out. If a subscriber is too slow and has maxsize set, drop.
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                log.warning("Dropping event for slow subscriber: %s", getattr(event, "type", event))
