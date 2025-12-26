from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Optional

from .config_loader import AppConfig
from .event_bus import EventBus
from .util.logging_setup import setup_logging

log = logging.getLogger(__name__)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="dustcollector")
    ap.add_argument("--config", required=True, help="Path to config YAML")
    return ap.parse_args(argv)


def _hw_mode_from_env() -> str:
    hw_mode = os.environ.get("DUSTCOLLECTOR_HW", "mock").strip().lower()
    if hw_mode not in ("mock", "real"):
        raise ValueError("DUSTCOLLECTOR_HW must be 'mock' or 'real'")
    return hw_mode


async def _event_logger(bus: EventBus) -> None:
    q = bus.subscribe(maxsize=100)
    try:
        while True:
            ev = await q.get()
            log.info("EVENT: %-10s src=%s data=%s", ev.type, ev.src, ev.data)
    except asyncio.CancelledError:
        log.info("Event logger cancelled")
        raise


async def _run_app(config_path: str) -> None:
    setup_logging()

    hw_mode = _hw_mode_from_env()
    is_mock = hw_mode == "mock"

    _ = AppConfig.load(config_path)
    log.info("Boot: hw_mode=%s is_mock=%s config=%s", hw_mode, is_mock, config_path)

    bus = EventBus()
    tasks: list[asyncio.Task[None]] = []

    # Always-on (quiet): event logger
    tasks.append(asyncio.create_task(_event_logger(bus), name="event_logger"))

    # Lathe controller: in mock mode, it drives Gate4 LEDs.
    from .tasks.lathe_gate_controller import run_lathe_gate_controller

    tasks.append(
        asyncio.create_task(run_lathe_gate_controller(bus), name="lathe_gate_ctrl")
    )
    log.info("Lathe gate controller enabled (Gate4 LED actuator)")

    # Lathe detector (A1) -> publishes events
    try:
        from .tasks.adc_watch import AdcWatchConfig, run_adc_watch

        adc_cfg = AdcWatchConfig(
            i2c_address=0x48,
            sample_hz=10.0,
            lathe_channel=1,
            lathe_on_threshold=0.040,
            lathe_off_threshold=0.025,
            consecutive_required=3,
        )
        tasks.append(asyncio.create_task(run_adc_watch(adc_cfg, bus), name="adc_watch"))
        log.info("ADC lathe detector enabled (quiet, evented)")
    except Exception:
        log.exception("ADC lathe detector failed to start")

    # Note: We intentionally do NOT run gate4_led_diag anymore.
    if is_mock:
        log.info("Mock mode: Gate4 LED diag disabled (Gate4 owned by controller)")

    try:
        while True:
            await asyncio.sleep(1.0)
    finally:
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        asyncio.run(_run_app(args.config))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
