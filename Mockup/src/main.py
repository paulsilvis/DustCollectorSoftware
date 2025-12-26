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
    # run.sh exports DUSTCOLLECTOR_HW as 'mock' or 'real'
    hw_mode = os.environ.get("DUSTCOLLECTOR_HW", "mock").strip().lower()
    if hw_mode not in ("mock", "real"):
        raise ValueError("DUSTCOLLECTOR_HW must be 'mock' or 'real'")
    return hw_mode


async def _run_app(config_path: str) -> None:
    setup_logging()

    hw_mode = _hw_mode_from_env()
    is_mock = hw_mode == "mock"

    cfg = AppConfig.load(config_path)

    log.info("Boot: hw_mode=%s is_mock=%s config=%s", hw_mode, is_mock, config_path)

    diag_task: Optional[asyncio.Task[None]] = None
    if is_mock:
        # Mock-only diagnostic: Gate4 LED blink via PCF8574.
        from .tasks.gate4_led_diag import PcfLedMapping, run_gate4_led_diag

        mapping = PcfLedMapping(
            bus=1,
            addr=0x20,
            green_bit=3,  # per your correction
            red_bit=7,    # per your correction
            active_low=True,
        )
        diag_task = asyncio.create_task(
            run_gate4_led_diag(mapping),
            name="gate4_led_diag",
        )
        log.info("Mock mode: Gate4 LED diagnostic enabled")
    else:
        log.info("Real mode: Gate4 LED diagnostic disabled")

    # If your existing app already starts tasks here, keep that code.
    # For now, idle forever until Ctrl+C.
    try:
        while True:
            await asyncio.sleep(1.0)
    finally:
        if diag_task is not None:
            diag_task.cancel()
            try:
                await diag_task
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
