from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Optional

from smbus2 import SMBus

from .config_loader import AppConfig
from .event_bus import EventBus
from .hardware.pcf_relays import PcfRelays, PcfRelaysConfig
from .util.logging_setup import setup_logging

log = logging.getLogger(__name__)

LED_PCF_ADDR = 0x20
RELAY_PCF_ADDR = 0x21


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


def _leds_all_off_boot() -> None:
    """
    Force all LEDs off at startup.

    Your LED bank on PCF8574 @ 0x20 is ACTIVE-HIGH:
      1 => LED ON
      0 => LED OFF
    Therefore OFF = 0x00.

    We write 0x00 then read back to confirm.
    """
    try:
        bus = SMBus(1)
        try:
            before = int(bus.read_byte(LED_PCF_ADDR))
            bus.write_byte(LED_PCF_ADDR, 0x00)
            after = int(bus.read_byte(LED_PCF_ADDR))
        finally:
            bus.close()

        log.info(
            "LED init: PCF@0x20 before=0x%02x wrote=0x00 after=0x%02x",
            before,
            after,
        )
    except Exception:
        log.exception("LED init: failed to force all-off at boot")


async def _run_app(config_path: str) -> None:
    setup_logging()

    hw_mode = _hw_mode_from_env()
    is_mock = hw_mode == "mock"

    _ = AppConfig.load(config_path)
    log.info("Boot: hw_mode=%s is_mock=%s config=%s", hw_mode, is_mock, config_path)

    # 1) LEDs off before any controller touches 0x20
    _leds_all_off_boot()

    bus = EventBus()
    tasks: list[asyncio.Task[None]] = []

    # 2) Relays on PCF8574 @ 0x21
    #
    # Hardware chain: PCF -> ULN2803 (inverts) -> relay board inputs (active-low).
    # Therefore: PCF bit=1 energizes relay => active_low=False at the PCF layer.
    relays = PcfRelays(PcfRelaysConfig(bus=1, addr=RELAY_PCF_ADDR, active_low=False))
    relay_lock = asyncio.Lock()

    # Startup safety: force all relays off under the same lock all controllers use.
    try:
        async with relay_lock:
            relays.all_off()
        log.info("Relay init: PCF@0x21 all OFF")
    except Exception:
        log.exception("Relay init: failed to force all-off at boot")

    # Event logger
    tasks.append(asyncio.create_task(_event_logger(bus), name="event_logger"))

    # Controllers (both use relays@0x21)
    from .tasks.lathe_gate_controller import run_lathe_gate_controller
    from .tasks.saw_gate_controller import run_saw_gate_controller

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

    # ADC watch (lathe-only per your file)
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

    if is_mock:
        log.info("Mock mode: running controllers; hardware may be absent")

    try:
        while True:
            await asyncio.sleep(3600.0)
    finally:
        log.info("Shutdown: cancelling tasks")
        for t in tasks:
            t.cancel()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip([t.get_name() for t in tasks], results):
            if isinstance(res, Exception) and not isinstance(res, asyncio.CancelledError):
                log.error("Task %s exited with error: %r", name, res)

        # Shutdown safety: force all relays OFF under lock
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
