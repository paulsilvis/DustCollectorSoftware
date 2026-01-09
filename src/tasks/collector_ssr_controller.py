from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from ..config_loader import AppConfig
from ..event_bus import EventBus
from ..events import Event

try:
    from ..hardware.gpio import GPIOOut
except Exception:  # pragma: no cover
    GPIOOut = None  # type: ignore

log = logging.getLogger(__name__)

LED_CTRL_PIN = 5  # BCM pin for LED strip control (active-high)

@dataclass(frozen=True)
class CollectorSsrConfig:
    pin_bcm: int = 25
    active_high: bool = True

    # Which tool events should drive the collector
    tools: tuple[str, ...] = ("saw", "lathe")


def _outputs_enabled(cfg: AppConfig) -> bool:
    hw = cfg.raw.get("hardware", {}) or {}
    return bool(hw.get("outputs_enabled", False))


def _load_cfg(app_cfg: AppConfig) -> CollectorSsrConfig:
    gpio = app_cfg.raw.get("gpio", {}) or {}
    pin = int(gpio.get("collector_ssr", 25))
    active_high = bool(gpio.get("collector_ssr_active_high", True))

    tools_raw = gpio.get("collector_tools", None)
    if tools_raw is None:
        tools = ("saw", "lathe")
    elif isinstance(tools_raw, (list, tuple)):
        tools = tuple(str(x).strip().lower() for x in tools_raw if str(x).strip())
    else:
        tools = ("saw", "lathe")

    return CollectorSsrConfig(pin_bcm=pin, active_high=active_high, tools=tools)


async def run_collector_ssr_controller(bus: EventBus, app_cfg: AppConfig) -> None:
    """
    Collector SSR controller.

    Policy:
    - If ANY configured tool is ON -> SSR ON immediately.
    - If ALL configured tools are OFF -> SSR OFF immediately.
    - No delay-off (per Paul's instruction).

    Event inputs:
    - Expects tool-specific events like: "lathe.on", "lathe.off", "saw.on", "saw.off"
      (published by adc_watch.py)
    """
    cfg = _load_cfg(app_cfg)

    # In mock mode or when outputs are inhibited, we should never touch real GPIO.
    if app_cfg.mock or not _outputs_enabled(app_cfg):
        log.info(
            "Collector SSR controller disabled (mock=%s outputs_enabled=%s)",
            app_cfg.mock,
            _outputs_enabled(app_cfg),
        )
        # Still consume events so behavior is testable in logs if desired.
        q = bus.subscribe()
        active: set[str] = set()
        try:
            while True:
                ev = await q.get()
                if not isinstance(ev, Event):
                    continue
                for tool in cfg.tools:
                    if ev.type == f"{tool}.on":
                        active.add(tool)
                    elif ev.type == f"{tool}.off":
                        active.discard(tool)
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise
    
    if GPIOOut is None:
        raise RuntimeError("RPi.GPIO not available but hardware.mode is real and outputs_enabled is true")
    # early exit here if in mock mode

    led_strip_control = GPIOOut(LED_CTRL_PIN, active_high=True)
    ssr = GPIOOut(cfg.pin_bcm, active_high=cfg.active_high)

    def blower_on() -> None:
        led_strip_control.on()
        ssr.on()

    def blower_off() -> None:
        led_strip_control.off()
        ssr.off()
 
    blower_off()
    ssr_on = False
    log.info(
        "Collector SSR controller ready (pin=%s active_high=%s tools=%s) [OFF]",
        cfg.pin_bcm,
        cfg.active_high,
        list(cfg.tools),
    )

    q = bus.subscribe()
    active: set[str] = set()

    try:
        while True:
            ev = await q.get()
            if not isinstance(ev, Event):
                continue

            changed = False
            for tool in cfg.tools:
                if ev.type == f"{tool}.on":
                    if tool not in active:
                        active.add(tool)
                        changed = True
                elif ev.type == f"{tool}.off":
                    if tool in active:
                        active.remove(tool)
                        changed = True

            if not changed:
                continue

            want_on = bool(active)
            if want_on and not ssr_on:
                blower_on()
                ssr_on = True
                log.info("Collector ON (active=%s)", sorted(active))
            elif (not want_on) and ssr_on:
                blower_off()
                ssr_on = False
                log.info("Collector OFF")

            await asyncio.sleep(0)
    except asyncio.CancelledError:
        log.info("Collector SSR controller cancelled; forcing OFF")
        try:
            blower_off()
        except Exception:
            log.exception("Collector SSR: failed to force OFF on shutdown")
        raise
