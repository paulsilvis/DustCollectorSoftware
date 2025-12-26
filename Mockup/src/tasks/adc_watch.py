from __future__ import annotations
import asyncio
import time
import logging
import random
from typing import Optional

from ..events import Event
from ..hardware.ads1115 import ADS1115Reader
from ..event_bus import EventBus

log = logging.getLogger("adc_watch")


class Debounce:
    def __init__(self, on_th, off_th, on_ms, off_ms):
        self.on_th = on_th
        self.off_th = off_th
        self.on_s = on_ms / 1000.0
        self.off_s = off_ms / 1000.0
        self.state = False
        self.t_ref = None

    def update(self, value: float, now: float) -> bool | None:
        target = True if not self.state else False
        th = self.on_th if target else self.off_th
        hold = self.on_s if target else self.off_s
        cond = value >= th if target else value <= th
        if cond:
            if self.t_ref is None:
                self.t_ref = now
            elif now - self.t_ref >= hold:
                self.state = target
                self.t_ref = None
                return self.state
        else:
            self.t_ref = None
        return None


def _mock_mode(cfg) -> str:
    ms = cfg.raw.get("mock_sim", {})
    mode = str(ms.get("mode", "pathological")).strip().lower()
    return mode if mode in ("realistic", "pathological") else "pathological"


def _mock_value(cfg, tool_index: int, now: float) -> float:
    ms = cfg.raw.get("mock_sim", {})
    mode = _mock_mode(cfg)

    cycle = float(ms.get("cycle_s", 14))
    on_s = float(ms.get("on_s", 6))
    off_mean = float(ms.get("off_mean_v", 0.05))
    on_mean = float(ms.get("on_mean_v", 0.55))
    noise = float(ms.get("noise_v", 0.02))

    if mode == "realistic":
        # Only ONE tool is "on" per cycle, sequentially.
        n = int(ms.get("tools", 4))
        slot = cycle / max(1, n)
        cur_tool = int((now % cycle) // slot) % max(1, n)
        mean = on_mean if tool_index == cur_tool and (now % slot) < on_s else off_mean
    else:
        # Pathological: staggered phases so multiple tools can overlap.
        phase = (now + tool_index * (cycle / 4.0)) % cycle
        mean = on_mean if phase < on_s else off_mean

    return max(0.0, min(1.0, random.gauss(mean, noise)))


async def adc_watch(bus: EventBus, cfg, hw):
    gates = cfg.raw["gates"]["map"]
    on_th = cfg.raw["debounce"]["on_threshold"]
    off_th = cfg.raw["debounce"]["off_threshold"]
    on_ms = cfg.raw["debounce"]["on_min_ms"]
    off_ms = cfg.raw["debounce"]["off_min_ms"]
    deb = {name: Debounce(on_th, off_th, on_ms, off_ms) for name in gates}

    ads = None
    if not cfg.mock:
        ads = ADS1115Reader(addr=cfg.raw["i2c"]["ads1115_addr"])

    ms = cfg.raw.get("mock_sim", {})
    tick = float(ms.get("tick_s", 0.2))

    log.info("adc_watch started (%s) [mock_mode=%s]", "MOCK" if cfg.mock else "REAL", _mock_mode(cfg))
    tool_names = list(gates.keys())

    while True:
        now = time.monotonic()
        for idx, name in enumerate(tool_names):
            ch = gates[name]["adc_ch"]
            if cfg.mock:
                volts = _mock_value(cfg, idx, now)
            else:
                assert ads is not None
                volts = ads.read_volts(ch)
            edge = deb[name].update(volts, now)
            if edge is True:
                await bus.publish(Event.now("machine.on", f"adc.{name}", tool=name, volts=volts))
            elif edge is False:
                await bus.publish(Event.now("machine.off", f"adc.{name}", tool=name, volts=volts))
        await asyncio.sleep(tick)
