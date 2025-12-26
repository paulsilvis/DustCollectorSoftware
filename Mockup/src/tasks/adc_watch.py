from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Optional

from ..event_bus import EventBus
from ..events import Event
from ..hardware.ads1115 import ADS1115Reader

log = logging.getLogger("adc_watch")


class Debounce:
    def __init__(self, on_th, off_th, on_ms, off_ms):
        self.on_th = on_th
        self.off_th = off_th
        self.on_ms = on_ms / 1000.0
        self.off_ms = off_ms / 1000.0
        self.state = False
        self._t_above: Optional[float] = None
        self._t_below: Optional[float] = None

    def update(self, volts: float, now: float) -> Optional[bool]:
        """
        Returns:
            True  -> rising edge (OFF -> ON)
            False -> falling edge (ON -> OFF)
            None  -> no edge
        """
        if not self.state:
            if volts >= self.on_th:
                if self._t_above is None:
                    self._t_above = now
                if (now - self._t_above) >= self.on_ms:
                    self.state = True
                    self._t_above = None
                    self._t_below = None
                    return True
            else:
                self._t_above = None
        else:
            if volts <= self.off_th:
                if self._t_below is None:
                    self._t_below = now
                if (now - self._t_below) >= self.off_ms:
                    self.state = False
                    self._t_above = None
                    self._t_below = None
                    return False
            else:
                self._t_below = None

        return None


def _mock_mode(cfg) -> str:
    mode = str(cfg.raw.get("mock_sim", {}).get("mode", "pathological")).strip().lower()
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
        #
        # NOTE: To create an "all tools off" gap, you must have:
        #   on_s < slot,  where slot = cycle_s / tools
        #
        # If on_s >= slot, one tool is ALWAYS on, so the collector never turns off.
        n = int(ms.get("tools", 4))
        n = max(1, n)
        slot = cycle / n

        if on_s >= slot:
            # Keep the sim usable even with "too large" on_s.
            # Example: cycle_s=14, tools=4 => slot=3.5s; on_s=4s would be always-on.
            log.warning(
                "mock_sim: on_s (%.3fs) >= slot (%.3fs); clamping on_s to 80%% of slot to allow OFF intervals",
                on_s,
                slot,
            )
            on_s = 0.8 * slot

        phase_in_cycle = now % cycle
        cur_tool = int(phase_in_cycle // slot) % n
        phase_in_slot = phase_in_cycle % slot

        mean = on_mean if (tool_index == cur_tool and phase_in_slot < on_s) else off_mean
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
        ads = ADS1115Reader(hw.i2c, cfg.raw["i2c"]["ads1115_addr"])

    tick = float(cfg.raw.get("adc", {}).get("tick_s", 0.25))

    log.info(
        "adc_watch started (%s) [mock_mode=%s]",
        "MOCK" if cfg.mock else "REAL",
        _mock_mode(cfg) if cfg.mock else "n/a",
    )

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
                await bus.publish(
                    Event.now("machine.on", f"adc.{name}", tool=name, volts=volts)
                )
            elif edge is False:
                await bus.publish(
                    Event.now("machine.off", f"adc.{name}", tool=name, volts=volts)
                )

        await asyncio.sleep(tick)
