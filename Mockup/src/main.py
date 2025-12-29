from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Optional

from .config_loader import AppConfig
from .event_bus import EventBus
from .hardware.pcf_relays import PcfRelays, PcfRelaysConfig
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

    # Shared relays @ 0x21 + shared lock for atomic read/modify/write
    relays = PcfRelays(PcfRelaysConfig(bus=1, addr=0x21, active_low=True))
    relay_lock = asyncio.Lock()
    try:
        relays.all_off()
    except Exception:
        log.exception("Relay init: failed to force all-off at boot")

    tasks.append(asyncio.create_task(_event_logger(bus), name="event_logger"))

    from .tasks.lathe_gate_controller import run_lathe_gate_controller
    from .tasks.saw_gate_controller import run_saw_gate_controller
    from .tasks.adc_watch import AdcWatchConfig, run_adc_watch

    tasks.append(
        asyncio.create_task(
            run_lathe_gate_controller(bus, relays, relay_lock),
            name="lathe_gate_ctrl",
        )
    )
    log.info("Lathe gate controller enabled")

    tasks.append(
        asyncio.create_task(
            run_saw_gate_controller(bus, relays, relay_lock),
            name="saw_gate_ctrl",
        )
    )
    log.info("Saw gate controller enabled")

    adc_cfg = AdcWatchConfig(
        i2c_address=0x48,
        sample_hz=10.0,
        saw_channel=0,
        lathe_channel=1,
        saw_on_threshold=1.00,
        saw_off_threshold=0.30,
        lathe_on_threshold=0.040,
        lathe_off_threshold=0.025,
        consecutive_required=3,
    )
    tasks.append(asyncio.create_task(run_adc_watch(adc_cfg, bus), name="adc_watch"))
    log.info("ADC detector enabled (quiet, evented)")

    if is_mock:
        log.info("Mock mode: controllers still run; sensors may be absent")

    try:
        while True:
            await asyncio.sleep(3600.0)
    finally:
        log.info("Shutdown: cancelling tasks")
        for t in tasks:
            t.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip([t.get_name() for t in tasks], results):
            if isinstance(res, Exception) and not isinstance(
                res, asyncio.CancelledError
            ):
                log.error("Task %s exited with error: %r", name, res)

        try:
            async with relay_lock:
                relays.all_off()
        except Exception:
            log.exception("Shutdown: failed to force all relays off")

        try:
            relays.close(restore=False)
        except Exception:
            log.exception("Shutdown: failed to close relay bus")

        log.info("Shutdown complete")


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        asyncio.run(_run_app(args.config))
        return 0
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt: exiting")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
