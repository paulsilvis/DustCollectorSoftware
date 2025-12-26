from __future__ import annotations
import asyncio
import logging
from ..events import Event

log = logging.getLogger("aqm_reader")


async def aqm_reader(queue, cfg, hw):
    # Open serial0 @ 9600 and parse PMS1003 frames (stub for now)
    log.info("aqm_reader started (stub)")
    while True:
        await asyncio.sleep(1.0)
