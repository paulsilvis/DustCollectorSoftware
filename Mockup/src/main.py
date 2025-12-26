from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Optional

from .config_loader import AppConfig
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


async def _run_app(config_path: str) -> None:
    setup_logging()

    hw_mode = _hw_mode_from_env()
    is_mock = hw_mode == "mock"

    _ = AppConfig.load(config_path)
    log.info("Boot: hw_mode=%s is_mock=%s config=%s", hw_mode, is_mock, config_path)

    tasks: list[asyncio.Task[None]] = []

    # MOCK-ONLY: Gate4 LED diagnostic
    if is_mock:
        from .tasks.gate4_led_diag import PcfLedMapping, run_gate4_led_diag

        mapping = PcfLedMapping(
            bus=1,
            addr=0x20,
            green_bit=3,
            red_bit=7,
            active_low=True,
        )
        tasks.append(
            asyncio.create_task(run_gate4_led_diag(mapping), name="gate4_led_diag")
        )
        log.info("Mock mode: Gate4 LED diagnostic enabled")

    # Quiet lathe detector (A1)
    try:
        from .tasks.adc_watch import AdcWatchConfig, run_adc_watch

        adc_cfg = AdcWatchConfig(
            i2c_address=0x48,
            sample_hz=10.0,
            lathe_channel=1,
            lathe_on_threshold=0.040,
            lathe_off_threshold=0.025,
            consecutive_required=3,
            heartbeat_sec=0.0,
        )
        tasks.append(
            asyncio.create_task(run_adc_watch(adc_cfg), name="adc_watch")
        )
        log.info("ADC lathe detector enabled (quiet)")
    except Exception:
        log.exception("ADC lathe detector failed to start")

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
