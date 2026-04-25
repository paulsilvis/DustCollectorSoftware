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
    tools: tuple[str, ...] = ("saw", "lathe")
    motor_delay_s: float = 0.0  # total delay from tool.on to motor start


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

    timing = app_cfg.raw.get("timing", {}) or {}
    gate_delay_s = float(timing.get("gate_delay_s", 0.0))
    solenoid_delay_s = float(timing.get("solenoid_delay_s", 0.0))
    motor_delay_s = gate_delay_s + solenoid_delay_s

    return CollectorSsrConfig(
        pin_bcm=pin,
        active_high=active_high,
        tools=tools,
        motor_delay_s=motor_delay_s,
    )


async def run_collector_ssr_controller(bus: EventBus, app_cfg: AppConfig) -> None:
    """
    Collector SSR controller.

    Policy:
    - If ANY configured tool is ON -> after motor_delay_s, SSR ON.
    - If ALL configured tools are OFF -> SSR OFF immediately (cancels any
      pending delayed start).
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
        raise RuntimeError(
            "RPi.GPIO not available but hardware.mode is real and outputs_enabled is true"
        )

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
    pending_on: asyncio.Task[None] | None = None

    log.info(
        "Collector SSR controller ready (pin=%s active_high=%s tools=%s "
        "motor_delay_s=%.1f) [OFF]",
        cfg.pin_bcm,
        cfg.active_high,
        list(cfg.tools),
        cfg.motor_delay_s,
    )

    q = bus.subscribe()
    active = set()

    async def _delayed_blower_on() -> None:
        """Sleep motor_delay_s then turn on if tools still active."""
        if cfg.motor_delay_s > 0:
            log.info(
                "Collector SSR: waiting %.1fs before motor start",
                cfg.motor_delay_s,
            )
            await asyncio.sleep(cfg.motor_delay_s)
        nonlocal ssr_on
        if active:  # still something running after the delay
            blower_on()
            ssr_on = True
            log.info("Collector ON (active=%s)", sorted(active))

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

            if want_on and not ssr_on and pending_on is None:
                # Schedule delayed motor start
                pending_on = asyncio.create_task(_delayed_blower_on())

            elif not want_on:
                # Tool(s) all off — cancel any pending start and stop motor now
                if pending_on is not None:
                    pending_on.cancel()
                    try:
                        await pending_on
                    except asyncio.CancelledError:
                        pass
                    pending_on = None
                if ssr_on:
                    blower_off()
                    ssr_on = False
                    log.info("Collector OFF")

            # Clean up completed pending task
            if pending_on is not None and pending_on.done():
                pending_on = None

            await asyncio.sleep(0)

    except asyncio.CancelledError:
        log.info("Collector SSR controller cancelled; forcing OFF")
        if pending_on is not None:
            pending_on.cancel()
        try:
            blower_off()
        except Exception:
            log.exception("Collector SSR: failed to force OFF on shutdown")
        raise
