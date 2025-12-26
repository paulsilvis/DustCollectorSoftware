from __future__ import annotations
import asyncio
import logging
import random
import time

from ..events import Event
from ..event_bus import EventBus

log = logging.getLogger("pms1003")

START1 = 0x42
START2 = 0x4D


def _checksum_ok(frame: bytes) -> bool:
    s = sum(frame[0:-2]) & 0xFFFF
    cs = (frame[-2] << 8) | frame[-1]
    return s == cs


def _parse(frame: bytes):
    if len(frame) < 32:
        return None
    pm2_5 = (frame[12] << 8) | frame[13]
    pm1_0 = (frame[10] << 8) | frame[11]
    pm10 = (frame[14] << 8) | frame[15]
    return {"pm1_0": pm1_0, "pm2_5": pm2_5, "pm10": pm10}


async def _mock_aqm(bus: EventBus, cfg):
    ms = cfg.raw.get("mock_sim", {})
    base = int(ms.get("pm25_base", 8))
    bump = int(ms.get("pm25_bump", 45))
    bump_s = float(ms.get("pm25_bump_s", 8))
    bad_th = cfg.raw["aqm"]["bad_threshold"]
    sev_th = cfg.raw["aqm"]["severe_threshold"]

    t0 = time.monotonic()
    log.info("PMS1003 mock stream running")
    while True:
        t = time.monotonic() - t0
        in_bump = (t % 30.0) < bump_s
        pm25 = base + (bump if in_bump else 0) + int(random.gauss(0, 2))
        pm25 = max(0, pm25)
        metrics = {"pm1_0": max(0, pm25 - 3), "pm2_5": pm25, "pm10": pm25 + 6}
        await bus.publish(Event.now("aqm.metrics", "aqm.mock", **metrics))
        bad = pm25 >= bad_th
        severe = pm25 >= sev_th
        await bus.publish(
            Event.now(
                "aqm.bad" if bad else "aqm.good",
                "aqm.mock",
                pm2_5=pm25,
                severe=severe,
            )
        )
        await asyncio.sleep(1.0)


async def aqm_reader(bus: EventBus, cfg, hw):
    if cfg.mock:
        await _mock_aqm(bus, cfg)
        return

    ser = hw.ser
    buf = bytearray()
    log.info("PMS1003 reader running")
    while True:
        await asyncio.sleep(0)
        data = ser.read(64)
        if not data:
            await asyncio.sleep(0.05)
            continue
        buf.extend(data)
        while len(buf) >= 32:
            if buf[0] != START1 or (len(buf) > 1 and buf[1] != START2):
                buf.pop(0)
                continue
            frame = bytes(buf[:32])
            del buf[:32]
            if not _checksum_ok(frame):
                continue
            metrics = _parse(frame)
            if not metrics:
                continue
            pm25 = metrics["pm2_5"]
            await bus.publish(Event.now("aqm.metrics", "aqm.pms1003", **metrics))
            bad = pm25 >= cfg.raw["aqm"]["bad_threshold"]
            severe = pm25 >= cfg.raw["aqm"]["severe_threshold"]
            await bus.publish(
                Event.now(
                    "aqm.bad" if bad else "aqm.good",
                    "aqm.pms1003",
                    pm2_5=pm25,
                    severe=severe,
                )
            )
