from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, List
from asyncio import Queue

log = logging.getLogger(__name__)


@dataclass(slots=True)
class DeviceEvent:
    """
    Simple device event for gate controllers.

    name: logical device name, e.g. "saw", "lathe"
    kind: "on" or "off" (for now; can be extended later)
    payload: optional extra info (e.g. ADC sample, timestamp)
    """
    name: str
    kind: str
    payload: Any = None

    def __post_init__(self) -> None:
        if self.kind not in ("on", "off"):
            raise ValueError(f"Invalid DeviceEvent.kind={self.kind!r}")


class EventBus:
    """
    Very small broadcast event bus.

    - subscribe(maxsize) -> asyncio.Queue[DeviceEvent]
    - publish(event)     -> fan-out to all subscriber queues

    No topics, no routing, just broadcast + local filtering,
    which is plenty for a 4–device shop system.
    """

    def __init__(self) -> None:
        self._subs: List[Queue[DeviceEvent]] = []
        self._lock = asyncio.Lock()

    def subscribe(self, maxsize: int = 0) -> Queue[DeviceEvent]:
        q: Queue[DeviceEvent] = asyncio.Queue(maxsize=maxsize)
        self._subs.append(q)
        log.debug("EventBus: new subscriber (total=%d)", len(self._subs))
        return q

    async def publish(self, event: DeviceEvent) -> None:
        """
        Broadcast an event to all subscribers.

        If a subscriber queue is full, we drop the event for that subscriber
        and log a warning. This is acceptable for this system, where events
        are frequent but not critical logs.
        """
        async with self._lock:
            for q in list(self._subs):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    log.warning(
                        "EventBus: dropped event %r for a full subscriber queue",
                        event,
                    )
